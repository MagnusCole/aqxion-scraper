import hashlib, datetime as dt, re, logging, os, time, sqlite3
from urllib.parse import urljoin, urlparse
from selectolax.parser import HTMLParser
from slugify import slugify
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from difflib import SequenceMatcher

from db import init_db, upsert_post
from sources import search_urls_for
from rules import tag_item
from config import KEYWORDS, MAX_PER_KW, LOG_LEVEL
from alerts import alert_lead

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

# Rate limiting por dominio
domain_last_request = {}
DOMAIN_RATE_LIMIT = 0.3  # segundos entre requests al mismo dominio

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
    """Verificar si un post es duplicado usando similitud de texto"""
    con = None
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        
        # Buscar posts similares de las últimas 24 horas
        cur.execute("""
            SELECT title, body, url 
            FROM posts 
            WHERE keyword = ? 
            AND created_at > datetime('now', '-1 day')
            AND (title IS NOT NULL OR body IS NOT NULL)
        """, (keyword,))
        
        similar_posts = cur.fetchall()
        
        for existing_title, existing_body, existing_url in similar_posts:
            # Verificar similitud de títulos
            if existing_title and title:
                title_similarity = calculate_text_similarity(title, existing_title)
                if title_similarity > 0.85:  # 85% de similitud
                    return True
            
            # Verificar similitud de contenido
            if existing_body and body:
                body_similarity = calculate_text_similarity(body, existing_body)
                if body_similarity > 0.90:  # 90% de similitud para contenido
                    return True
            
            # Verificar URLs similares (mismo dominio + path similar)
            if existing_url and url:
                parsed_existing = urlparse(existing_url)
                parsed_new = urlparse(url)
                if (parsed_existing.netloc == parsed_new.netloc and 
                    calculate_text_similarity(parsed_existing.path, parsed_new.path) > 0.8):
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

def rate_limited_get(url: str, session):
    """Hacer request con rate limiting por dominio"""
    domain = urlparse(url).netloc
    
    # Rate limiting
    now = time.time()
    if domain in domain_last_request:
        time_since_last = now - domain_last_request[domain]
        if time_since_last < DOMAIN_RATE_LIMIT:
            time.sleep(DOMAIN_RATE_LIMIT - time_since_last)
    
    domain_last_request[domain] = time.time()
    
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        log.warning(f"Error fetching {url}: {e}")
        return None

# Logging setup
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

def run_once():
    init_db()
    keywords_to_use = KEYWORDS
    log.info(f"Iniciando scrape con {len(keywords_to_use)} keywords")
    total_processed = 0

    for kw in keywords_to_use:
        for url in search_urls_for(kw):
            scrape_url(url, kw)
            total_processed += 1

    log.info(f"Scrape completado. Procesadas {len(keywords_to_use)} keywords")

if __name__ == "__main__":
    run_once()
