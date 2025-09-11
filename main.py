import hashlib, datetime as dt, re, logging, os, time, sqlite3, asyncio
from urllib.parse import urljoin, urlparse
from selectolax.parser import HTMLParser
from slugify import slugify
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from difflib import SequenceMatcher
import aiohttp
from aiohttp import ClientTimeout

from db import init_db, upsert_post
from sources import search_urls_for
from rules import tag_item
from config import KEYWORDS, MAX_PER_KW, LOG_LEVEL
from alerts import alert_lead, AlertSystem, auto_configure_alerts, alert_system_status

DB_PATH = "scraping.db"

# Lista blanca de dominios permitidos (para scraping ético)
ALLOWED_DOMAINS = [
    'duckduckgo.com',
    'google.com',
    'bing.com',
    'yahoo.com',
    # Agregar más dominios según sea necesario
]

def check_robots_txt(domain: str) -> bool:
    """Verificar si el dominio permite scraping según robots.txt"""
    try:
        robots_url = f"https://{domain}/robots.txt"
        response = requests.get(robots_url, timeout=5)
        if response.status_code == 200:
            robots_content = response.text.lower()
            # Verificar si permite nuestro user agent
            if 'user-agent: *' in robots_content:
                # Buscar disallow para nuestro user agent
                lines = robots_content.split('\n')
                in_user_agent_section = False
                for line in lines:
                    line = line.strip()
                    if line.startswith('user-agent:'):
                        if '*' in line:
                            in_user_agent_section = True
                        else:
                            in_user_agent_section = False
                    elif in_user_agent_section and line.startswith('disallow:'):
                        path = line.replace('disallow:', '').strip()
                        if path == '/' or path == '':
                            log.warning(f"Robots.txt bloquea scraping completo en {domain}")
                            return False
                return True
        return True  # Si no hay robots.txt, asumir permitido
    except Exception as e:
        log.warning(f"Error verificando robots.txt para {domain}: {e}")
        return True  # En caso de error, permitir scraping

def is_domain_allowed(url: str) -> bool:
    """Verificar si el dominio está en la lista blanca"""
    domain = urlparse(url).netloc
    # Remover www. si existe
    domain = domain.replace('www.', '')
    
    # Verificar lista blanca
    for allowed in ALLOWED_DOMAINS:
        if allowed in domain:
            return True
    
    # Para dominios no en lista blanca, verificar robots.txt
    return check_robots_txt(domain)

# Rate limiting por dominio con backoff inteligente
domain_last_request = {}
domain_error_count = {}  # Contador de errores por dominio
domain_backoff_until = {}  # Timestamp hasta el cual hacer backoff
DOMAIN_RATE_LIMIT = 0.5  # segundos entre requests al mismo dominio (mejorado de 0.3 a 0.5)
MAX_BACKOFF_DELAY = 30  # máximo delay en segundos
BACKOFF_MULTIPLIER = 2  # multiplicador para backoff exponencial

def make_id(url: str, title: str, body: str | None) -> str:
    """Generar ID único para un post basado en URL, título y contenido"""
    base = f"{url}|{slugify(title or '')}|{(body or '')[:120]}".encode()
    return hashlib.sha256(base).hexdigest()[:16]

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calcular similitud entre dos textos usando SequenceMatcher"""
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def is_duplicate_post(title: str, body: str | None, url: str, keyword: str) -> bool:
    """Verificar si un post es duplicado usando múltiples estrategias"""
    con = None
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()

        # 1. PRIMERO: Verificar URL exacta (más rápido)
        cur.execute("""
            SELECT COUNT(*) FROM posts
            WHERE url = ? AND created_at > datetime('now', '-7 day')
        """, (url,))

        if cur.fetchone()[0] > 0:
            return True

        # 2. Verificar similitud de títulos (solo si no hay match exacto de URL)
        if title:
            # Buscar títulos similares en las últimas 24 horas
            cur.execute("""
                SELECT title FROM posts
                WHERE keyword = ?
                AND created_at > datetime('now', '-1 day')
                AND title IS NOT NULL
                AND LENGTH(title) > 10
            """, (keyword,))

            existing_titles = cur.fetchall()

            for (existing_title,) in existing_titles:
                if existing_title and len(existing_title) > 10:
                    title_similarity = calculate_text_similarity(title, existing_title)
                    if title_similarity > 0.85:  # 85% de similitud
                        log.debug(f"Duplicado detectado por título similar: '{title[:50]}...' ~ '{existing_title[:50]}...'")
                        return True

        # 3. Verificar similitud de contenido (solo para contenido sustancial)
        if body and len(body.strip()) > 100:
            # Crear hash del contenido para comparación rápida
            import hashlib
            body_hash = hashlib.md5(body.strip()[:500].encode()).hexdigest()

            cur.execute("""
                SELECT COUNT(*) FROM posts
                WHERE keyword = ?
                AND created_at > datetime('now', '-3 day')
                AND body IS NOT NULL
                AND LENGTH(body) > 100
            """, (keyword,))

            # Si hay muchos posts, usar comparación de hash aproximada
            if cur.fetchone()[0] > 50:
                # Comparar con posts más recientes y de alta calidad
                cur.execute("""
                    SELECT body FROM posts
                    WHERE keyword = ?
                    AND created_at > datetime('now', '-1 day')
                    AND body IS NOT NULL
                    AND LENGTH(body) > 100
                    AND relevance_score > 70
                    ORDER BY created_at DESC
                    LIMIT 20
                """, (keyword,))

                recent_bodies = cur.fetchall()

                for (existing_body,) in recent_bodies:
                    if existing_body:
                        # Comparación rápida de hash
                        existing_hash = hashlib.md5(existing_body.strip()[:500].encode()).hexdigest()
                        if body_hash == existing_hash:
                            log.debug(f"Duplicado detectado por hash de contenido idéntico")
                            return True

                        # Si hash no coincide, verificar similitud de texto
                        body_similarity = calculate_text_similarity(body[:300], existing_body[:300])
                        if body_similarity > 0.90:  # 90% de similitud
                            log.debug(f"Duplicado detectado por contenido similar: {body_similarity:.2f}")
                            return True

        # 4. Verificar URLs similares (mismo dominio + path similar)
        if url:
            parsed_new = urlparse(url)
            domain = parsed_new.netloc
            path = parsed_new.path

            # Buscar URLs del mismo dominio con paths similares
            cur.execute("""
                SELECT url FROM posts
                WHERE url LIKE ?
                AND created_at > datetime('now', '-2 day')
            """, (f"%{domain}%",))

            similar_urls = cur.fetchall()

            for (existing_url,) in similar_urls:
                if existing_url and existing_url != url:
                    parsed_existing = urlparse(existing_url)
                    if parsed_existing.netloc == domain:
                        # Comparar paths
                        path_similarity = calculate_text_similarity(parsed_existing.path, path)
                        if path_similarity > 0.8:
                            log.debug(f"Duplicado detectado por URL similar: {existing_url} ~ {url}")
                            return True

        return False

    except sqlite3.Error as e:
        log.warning(f"Error verificando duplicados: {e}")
        return False
    finally:
        if con:
            con.close()

def validate_content_quality(title: str, body: str | None, url: str) -> tuple[bool, str]:
    """Validar calidad del contenido y detectar spam"""
    # Validar longitud mínima
    if len(title.strip()) < 10:
        return False, "Título demasiado corto"
    
    if body and len(body.strip()) < 20:
        return False, "Contenido demasiado corto"
    
    # Detectar spam patterns
    spam_patterns = [
        r'\b(?:viagra|casino|lottery|winner|prize)\b',
        r'(?:http|https|www\.)\S{50,}',  # URLs muy largas
        r'\b\d{10,}\b',  # Números largos (posible teléfono spam)
        r'[A-Z]{5,}',  # Texto en mayúsculas excesivo
        r'(.)\1{4,}',  # Caracteres repetidos
    ]
    
    text_to_check = f"{title} {body or ''}".lower()
    
    for pattern in spam_patterns:
        if re.search(pattern, text_to_check, re.IGNORECASE):
            return False, f"Detectado patrón de spam: {pattern}"
    
    # Verificar que tenga palabras reales (no solo símbolos)
    words = re.findall(r'\b\w{3,}\b', text_to_check)
    if len(words) < 3:
        return False, "Contenido insuficiente o no legible"
    
    return True, "Contenido válido"

def calculate_relevance_score(tag: str, title: str, body: str | None) -> int:
    """Calcular score de relevancia basado en tipo de intención y calidad del contenido"""
    base_score = 0
    
    # Score base por tipo de intención (dolor > búsqueda > objeción > ruido)
    if tag == 'dolor':
        base_score = 100
    elif tag == 'busqueda':
        base_score = 75
    elif tag == 'objecion':
        base_score = 50
    else:  # ruido
        base_score = 10
    
    # Bonus por calidad del contenido
    content_bonus = 0
    
    # Longitud del título
    title_length = len(title.strip())
    if title_length > 50:
        content_bonus += 10
    elif title_length > 30:
        content_bonus += 5
    
    # Longitud del body
    if body:
        body_length = len(body.strip())
        if body_length > 200:
            content_bonus += 15
        elif body_length > 100:
            content_bonus += 10
        elif body_length > 50:
            content_bonus += 5
    
    # Palabras clave de urgencia
    urgent_words = ['urgente', 'inmediato', 'ya', 'necesito', 'ayuda', 'problema']
    text_to_check = f"{title} {body or ''}".lower()
    urgent_count = sum(1 for word in urgent_words if word in text_to_check)
    content_bonus += urgent_count * 5
    
    return min(base_score + content_bonus, 150)  # Máximo 150

def analyze_intention_advanced(text: str) -> str:
    """Análisis avanzado de intenciones usando regex mejorado + lógica para casos dudosos"""
    text_lower = text.lower()
    
    # Primero usar regex existentes
    from rules import tag_item
    primary_tag = tag_item(text)
    
    # Si es claramente identificado, devolverlo
    if primary_tag != 'ruido':
        return primary_tag
    
    # Para casos dudosos (clasificados como ruido), aplicar lógica adicional
    doubt_patterns = {
        'dolor': [
            r'no\s+funciona', r'está\s+mal', r'problemas\s+con', r'no\s+puedo',
            r'ayuda\s+con', r'tengo\s+un\s+problema', r'error\s+en', r'fallando'
        ],
        'busqueda': [
            r'busco\s+a', r'necesito\s+un', r'dónde\s+encontrar', r'quién\s+tiene',
            r'recomiendan\s+a', r'proveedor\s+de', r'cotización\s+para'
        ],
        'objecion': [
            r'muy\s+caro', r'precio\s+alto', r'no\s+me\s+convence', r'mala\s+experiencia',
            r'problemas\s+de', r'no\s+confío', r'insatisfecho\s+con'
        ]
    }
    
    # Contar matches por categoría
    scores = {'dolor': 0, 'busqueda': 0, 'objecion': 0}
    
    for category, patterns in doubt_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                scores[category] += 1
    
    # Si hay al menos un match claro, usar esa categoría
    max_score = max(scores.values())
    if max_score > 0:
        for category, score in scores.items():
            if score == max_score:
                return category
    
    # Si sigue siendo dudoso, devolver ruido
    return 'ruido'

def should_scrape_detail(url: str, title: str, keyword: str) -> tuple[bool, str]:
    """
    Filtrado avanzado antes de hacer request detallada.
    Retorna (should_scrape, reason)
    """
    # 1. Filtrado por palabras irrelevantes en título
    irrelevant_words = [
        'login', 'register', 'sign in', 'sign up', 'subscribe', 'newsletter',
        'advertisement', 'ads', 'sponsored', 'promo', 'promotion',
        'cookie', 'privacy', 'terms', 'contact', 'about us', 'faq',
        'copyright', 'all rights reserved', 'menu', 'navigation'
    ]
    
    title_lower = title.lower()
    if any(word in title_lower for word in irrelevant_words):
        return False, "título irrelevante"
    
    # 2. Filtrado por patrones de URL irrelevantes
    irrelevant_url_patterns = [
        '/tag/', '/category/', '/author/', '/archive/', '/page/',
        '/search', '/feed', '/rss', '/comments', '/reply',
        '/login', '/register', '/admin', '/wp-admin', '/wp-login',
        '/user', '/profile', '/account', '/settings'
    ]
    
    url_lower = url.lower()
    if any(pattern in url_lower for pattern in irrelevant_url_patterns):
        return False, "patrón URL irrelevante"
    
    # 3. Filtrado por longitud mínima de título
    if len(title.strip()) < 15:
        return False, "título demasiado corto"
    
    # 4. Filtrado por calidad de título (debe contener al menos una palabra de más de 4 letras)
    words = title.split()
    long_words = [w for w in words if len(w) > 4]
    if len(long_words) < 1:
        return False, "título de baja calidad"
    
    # 5. Verificar que el título contenga la keyword o términos relacionados
    keyword_lower = keyword.lower()
    title_words = set(title_lower.split())
    keyword_words = set(keyword_lower.split())
    
    # Al menos una palabra del keyword debe aparecer en el título
    if not keyword_words.intersection(title_words):
        # O al menos el keyword completo
        if keyword_lower not in title_lower:
            return False, "título no relacionado con keyword"
    
    # 6. Filtrado por caracteres especiales excesivos
    special_chars = sum(1 for c in title if c in '!@#$%^&*()_+-=[]{}|;:,.<>?')
    if special_chars > len(title) * 0.3:  # Más del 30% son caracteres especiales
        return False, "exceso de caracteres especiales"
    
    # 7. Evitar títulos que parecen menús o navegación
    if title.count('|') > 2 or title.count('»') > 2 or title.count('>') > 2:
        return False, "parece menú de navegación"
    
    return True, "válido para scraping"

def create_session_with_retry():
    """Crear sesión HTTP con retry strategy"""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    return session

# Función para calcular similitud de texto (ya definida arriba)
# def calculate_text_similarity(text1: str, text2: str) -> float:

def rate_limited_get(url: str, session):
    """Hacer request con rate limiting inteligente y backoff"""
    domain = urlparse(url).netloc
    now = time.time()
    
    # Verificar si estamos en período de backoff
    if domain in domain_backoff_until and now < domain_backoff_until[domain]:
        remaining_backoff = domain_backoff_until[domain] - now
        log.warning(f"Backoff activo para {domain}, esperando {remaining_backoff:.1f}s")
        time.sleep(min(remaining_backoff, MAX_BACKOFF_DELAY))
        # Re-verificar después del sleep
        if time.time() < domain_backoff_until[domain]:
            log.error(f"Backoff máximo excedido para {domain}")
            return None
    
    # Rate limiting normal
    if domain in domain_last_request:
        time_since_last = now - domain_last_request[domain]
        base_delay = DOMAIN_RATE_LIMIT
        
        # Aplicar backoff adicional basado en errores previos
        error_count = domain_error_count.get(domain, 0)
        if error_count > 0:
            backoff_delay = min(base_delay * (BACKOFF_MULTIPLIER ** error_count), MAX_BACKOFF_DELAY)
            base_delay = backoff_delay
        
        if time_since_last < base_delay:
            actual_delay = base_delay - time_since_last
            log.debug(f"Rate limiting: esperando {actual_delay:.2f}s para {domain}")
            time.sleep(actual_delay)
    
    domain_last_request[domain] = time.time()
    
    try:
        response = session.get(url, timeout=15)  # Aumentar timeout
        response.raise_for_status()
        
        # Resetear contador de errores en caso de éxito
        if domain in domain_error_count:
            domain_error_count[domain] = 0
            if domain in domain_backoff_until:
                del domain_backoff_until[domain]
        
        return response
        
    except requests.RequestException as e:
        # Incrementar contador de errores
        domain_error_count[domain] = domain_error_count.get(domain, 0) + 1
        error_count = domain_error_count[domain]
        
        # Calcular backoff basado en tipo de error
        if hasattr(e.response, 'status_code') and e.response:
            status_code = e.response.status_code
            if status_code == 429:  # Too Many Requests
                backoff_seconds = min(60 * (BACKOFF_MULTIPLIER ** error_count), 300)  # Max 5 minutos
                domain_backoff_until[domain] = now + backoff_seconds
                log.warning(f"Rate limit hit para {domain} (429), backoff {backoff_seconds}s")
            elif status_code >= 500:  # Server errors
                backoff_seconds = min(30 * (BACKOFF_MULTIPLIER ** error_count), 120)  # Max 2 minutos
                domain_backoff_until[domain] = now + backoff_seconds
                log.warning(f"Server error {status_code} para {domain}, backoff {backoff_seconds}s")
            elif status_code == 403:  # Forbidden - posible bloqueo
                backoff_seconds = min(300 * (BACKOFF_MULTIPLIER ** error_count), 1800)  # Max 30 minutos
                domain_backoff_until[domain] = now + backoff_seconds
                log.warning(f"Access forbidden {status_code} para {domain}, backoff {backoff_seconds}s")
            else:
                # Otros errores 4xx
                backoff_seconds = min(10 * (BACKOFF_MULTIPLIER ** error_count), 60)  # Max 1 minuto
                domain_backoff_until[domain] = now + backoff_seconds
                log.warning(f"Client error {status_code} para {domain}, backoff {backoff_seconds}s")
        else:
            # Error de conexión o timeout
            backoff_seconds = min(5 * (BACKOFF_MULTIPLIER ** error_count), 30)  # Max 30 segundos
            domain_backoff_until[domain] = now + backoff_seconds
            log.warning(f"Connection error para {domain}, backoff {backoff_seconds}s")
        
        log.warning(f"Error fetching {url}: {e} (intento #{error_count})")
        return None

async def async_rate_limited_get(url: str, session: aiohttp.ClientSession):
    """Hacer request async con rate limiting inteligente y backoff"""
    domain = urlparse(url).netloc
    now = time.time()

    # Verificar si estamos en período de backoff
    if domain in domain_backoff_until and now < domain_backoff_until[domain]:
        remaining_backoff = domain_backoff_until[domain] - now
        log.warning(f"Backoff activo para {domain}, esperando {remaining_backoff:.1f}s")
        await asyncio.sleep(min(remaining_backoff, MAX_BACKOFF_DELAY))
        # Re-verificar después del sleep
        if time.time() < domain_backoff_until[domain]:
            log.error(f"Backoff máximo excedido para {domain}")
            return None

    # Rate limiting normal
    if domain in domain_last_request:
        time_since_last = now - domain_last_request[domain]
        base_delay = DOMAIN_RATE_LIMIT

        # Aplicar backoff adicional basado en errores previos
        error_count = domain_error_count.get(domain, 0)
        if error_count > 0:
            backoff_delay = min(base_delay * (BACKOFF_MULTIPLIER ** error_count), MAX_BACKOFF_DELAY)
            base_delay = backoff_delay

        if time_since_last < base_delay:
            actual_delay = base_delay - time_since_last
            log.debug(f"Rate limiting: esperando {actual_delay:.2f}s para {domain}")
            await asyncio.sleep(actual_delay)

    domain_last_request[domain] = time.time()

    try:
        timeout = ClientTimeout(total=15)
        async with session.get(url, timeout=timeout) as response:
            response.raise_for_status()

            # Resetear contador de errores en caso de éxito
            if domain in domain_error_count:
                domain_error_count[domain] = 0
                if domain in domain_backoff_until:
                    del domain_backoff_until[domain]

            return await response.text()

    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        # Incrementar contador de errores
        domain_error_count[domain] = domain_error_count.get(domain, 0) + 1
        error_count = domain_error_count[domain]

        # Para aiohttp, el status code no está disponible en la excepción
        # Usamos un backoff genérico para errores de red
        backoff_seconds = min(5 * (BACKOFF_MULTIPLIER ** error_count), 30)  # Max 30 segundos
        domain_backoff_until[domain] = now + backoff_seconds
        log.warning(f"Connection error para {domain}, backoff {backoff_seconds}s")

        log.warning(f"Error fetching {url}: {e} (intento #{error_count})")
        return None# Logging setup
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger("aqxion")

def scrape_url(url: str, keyword: str):
    # Verificar si el dominio permite scraping
    if not is_domain_allowed(url):
        log.warning(f"Saltando {url} - dominio no permitido o bloqueado por robots.txt")
        return
        
    now = dt.datetime.utcnow().isoformat()
    session = create_session_with_retry()
    
    try:
        response = rate_limited_get(url, session)
        if not response:
            return
            
        html = HTMLParser(response.text)
        count = 0
        for a in html.css("a"):
            if count >= MAX_PER_KW:
                break
            href = a.attributes.get("href", "")
            title = (a.text() or "").strip()
            if (not href or
                href.startswith("#") or
                any(x in href.lower() for x in ["javascript:", "mailto:", "tel:"]) or
                len(title) < 25):
                continue

            full_url = urljoin(url, href)
            if not full_url.startswith("http"):
                continue
                
            # Verificar robots.txt para el dominio del link
            if not is_domain_allowed(full_url):
                log.debug(f"Saltando link {full_url} - dominio no permitido")
                continue

            # FILTRADO AVANZADO ANTES DE REQUEST DETALLADA
            should_scrape, reason = should_scrape_detail(full_url, title, keyword)
            if not should_scrape:
                log.debug(f"Saltando link {full_url} - {reason}")
                continue

            # Extraer body y fecha siguiendo el link
            body = None
            published_at = None
            try:
                detail_response = rate_limited_get(full_url, session)
                if detail_response:
                    detail_html = HTMLParser(detail_response.text)
                    # Heurísticas para snippet
                    body = " ".join(t.strip() for t in detail_html.text().split())[:600]
                    # Fecha si existe
                    time_elem = detail_html.css_first("time")
                    if time_elem:
                        published_at = time_elem.attributes.get("datetime")

                    # Heurística adicional: meta[property="article:published_time"]
                    if not published_at:
                        meta_time = detail_html.css_first('meta[property="article:published_time"]')
                        if meta_time:
                            published_at = meta_time.attributes.get("content")
            except Exception as e:
                log.warning(f"Error extrayendo detalle de {full_url}: {e}")

            # Etiquetado de intención usando análisis avanzado
            text_for_tag = f"{title} {body or ''}"
            tag = analyze_intention_advanced(text_for_tag)

            # VALIDACIÓN DE CONTENIDO Y DEDUPLICACIÓN
            # 1. Validar calidad del contenido
            is_valid, validation_reason = validate_content_quality(title, body, full_url)
            if not is_valid:
                log.debug(f"Contenido rechazado: {validation_reason} - {title[:50]}...")
                continue
            
            # 2. Verificar duplicados
            if is_duplicate_post(title, body, full_url, keyword):
                log.debug(f"Post duplicado detectado: {title[:50]}...")
                continue

            # Normalizar y guardar
            relevance_score = calculate_relevance_score(tag, title, body)
            post = {
                "id": make_id(full_url, title, body),
                "source": "MVP",
                "url": full_url,
                "title": title[:300],
                "body": body,
                "lang": "es",
                "created_at": now,
                "keyword": keyword,
                "tag": tag,
                "published_at": published_at,
                "relevance_score": relevance_score,
            }
            upsert_post(post)

            # 🚨 ALERTAS PARA LEADS DE ALTO VALOR
            if tag in ['dolor', 'busqueda'] and relevance_score >= 80:
                alert_lead(title, body or "", full_url, keyword, tag, relevance_score)

            # ⚠️ ALERTA MANUAL: Mostrar posts relevantes en consola
            if tag in ["dolor", "busqueda"]:
                log.warning(f"⚠️ NUEVO {tag.upper()} | {keyword}: {title[:120]} — {full_url}")
                if body:
                    log.warning(f"   Snippet: {body[:100]}{'...' if len(body) > 100 else ''}")
                log.warning("-" * 80)

            count += 1

        log.info(f"Procesados {count} items de {url}")
    except Exception as e:
        log.error(f"Error scraping {url}: {e}")

# Función async para scrapear URLs con mejor paralelización
async def async_scrape_url(url: str, keyword: str, session: aiohttp.ClientSession):
    """Versión async de scrape_url para mejor paralelización"""
    # Verificar si el dominio permite scraping
    if not is_domain_allowed(url):
        log.warning(f"Saltando {url} - dominio no permitido o bloqueado por robots.txt")
        return

    now = dt.datetime.utcnow().isoformat()

    try:
        response_text = await async_rate_limited_get(url, session)
        if not response_text:
            return

        html = HTMLParser(response_text)
        count = 0

        # Procesar links de forma síncrona por ahora (podría paralelizarse más tarde)
        for a in html.css("a"):
            if count >= MAX_PER_KW:
                break
            href = a.attributes.get("href", "")
            title = (a.text() or "").strip()
            if (not href or
                href.startswith("#") or
                any(x in href.lower() for x in ["javascript:", "mailto:", "tel:"]) or
                len(title) < 25):
                continue

            full_url = urljoin(url, href)
            if not full_url.startswith("http"):
                continue

            # Verificar robots.txt para el dominio del link
            if not is_domain_allowed(full_url):
                log.debug(f"Saltando link {full_url} - dominio no permitido")
                continue

            # FILTRADO AVANZADO ANTES DE REQUEST DETALLADA
            should_scrape, reason = should_scrape_detail(full_url, title, keyword)
            if not should_scrape:
                log.debug(f"Saltando link {full_url} - {reason}")
                continue

            # Extraer body y fecha siguiendo el link
            body = None
            published_at = None
            try:
                detail_response_text = await async_rate_limited_get(full_url, session)
                if detail_response_text:
                    detail_html = HTMLParser(detail_response_text)
                    # Heurísticas para snippet
                    body = " ".join(t.strip() for t in detail_html.text().split())[:600]
                    # Fecha si existe
                    time_elem = detail_html.css_first("time")
                    if time_elem:
                        published_at = time_elem.attributes.get("datetime")

                    # Heurística adicional: meta[property="article:published_time"]
                    if not published_at:
                        meta_time = detail_html.css_first('meta[property="article:published_time"]')
                        if meta_time:
                            published_at = meta_time.attributes.get("content")
            except Exception as e:
                log.warning(f"Error extrayendo detalle de {full_url}: {e}")

            # Etiquetado de intención usando análisis avanzado
            text_for_tag = f"{title} {body or ''}"
            tag = analyze_intention_advanced(text_for_tag)

            # Calcular score de relevancia
            relevance_score = calculate_relevance_score(title, body or '', keyword)

            # Verificar duplicados
            if is_duplicate_post(title, body, full_url, keyword):
                log.debug(f"Post duplicado saltado: {title[:50]}...")
                continue

            # Crear post
            post = {
                'id': make_id(full_url, title, body),
                'source': urlparse(full_url).netloc,
                'url': full_url,
                'title': title,
                'body': body,
                'lang': 'es',  # Asumir español por defecto
                'created_at': now,
                'keyword': keyword,
                'tag': tag,
                'published_at': published_at,
                'relevance_score': relevance_score
            }

            # Guardar en base de datos
            upsert_post(post)

            # Alertar si es lead de alto valor
            if tag in ['dolor', 'busqueda'] and relevance_score >= 80:
                alert_lead(
                    title=title,
                    body=body or '',
                    url=full_url,
                    keyword=keyword,
                    tag=tag,
                    score=relevance_score
                )

            count += 1
            log.info(f"✅ Procesado: {title[:50]}... (tag: {tag}, score: {relevance_score})")

    except Exception as e:
        log.error(f"Error procesando {url}: {e}")

async def async_run_once():
    """Versión async de run_once para mejor paralelización"""
    log.info("🚀 Iniciando Aqxion Scraper (Async Version)")

    # Inicializar base de datos
    init_db()

    # Configurar alertas automáticamente
    auto_configure_alerts()
    alert_system_status("started", "Iniciando scraping async")

    keywords_to_use = KEYWORDS[:]
    log.info(f"Iniciando scrape async con {len(keywords_to_use)} keywords")

    # Crear sesión aiohttp
    timeout = ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(limit=10)  # Limitar conexiones concurrentes

    async with aiohttp.ClientSession(
        timeout=timeout,
        connector=connector,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    ) as session:

        total_processed = 0

        # Procesar keywords de forma secuencial, pero URLs de forma async dentro de cada keyword
        for kw in keywords_to_use:
            urls = search_urls_for(kw)
            log.info(f"Procesando keyword '{kw}' con {len(urls)} URLs")

            # Procesar URLs de forma concurrente para esta keyword
            tasks = [async_scrape_url(url, kw, session) for url in urls]
            await asyncio.gather(*tasks, return_exceptions=True)

            total_processed += len(urls)

        log.info(f"✅ Scrape async completado. Procesadas {len(keywords_to_use)} keywords, {total_processed} URLs")

def run_once():
    """Función síncrona original (mantenida por compatibilidad)"""
    log.info("🚀 Iniciando Aqxion Scraper (Sync Version)")

    # Inicializar base de datos
    init_db()

    # Configurar alertas automáticamente
    auto_configure_alerts()
    alert_system_status("started", "Iniciando scraping sync")

    keywords_to_use = KEYWORDS[:]
    log.info(f"Iniciando scrape con {len(keywords_to_use)} keywords")
    total_processed = 0

    for kw in keywords_to_use:
        for url in search_urls_for(kw):
            scrape_url(url, kw)
            total_processed += 1

    log.info(f"Scrape completado. Procesadas {len(keywords_to_use)} keywords")

async def run_async():
    """Punto de entrada para versión async"""
    await async_run_once()

if __name__ == "__main__":
    # Ejecutar versión async por defecto
    asyncio.run(run_async())
