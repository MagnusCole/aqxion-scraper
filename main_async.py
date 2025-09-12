"""
Aqxion Scraper v2.0 - Arquitectura completamente asÃ­ncrona
Reemplaza la implementaciÃ³n hÃ­brida sÃ­ncrona/asÃ­ncrona con un sistema consistente
"""

import asyncio
import hashlib
import datetime as dt
import re
import logging
import os
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set, Any
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass, asdict

import aiohttp
from aiohttp import ClientTimeout, ClientSession, TCPConnector
import aiofiles
from selectolax.parser import HTMLParser
from slugify import slugify
import pandas as pd
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configuración moderna
from config_v2 import get_settings, ScrapingSettings, DatabaseSettings
from db import init_db, upsert_post
from sources import search_urls_for
from rules import tag_item
from alerts import alert_lead, AlertSystem, auto_configure_alerts, alert_system_status
from cache_system import cache_manager
from scrapling_simple import scrapling_scraper

# ConfiguraciÃ³n
settings = get_settings()
scraping_config = settings.scraping
db_config = settings.database

# ConfiguraciÃ³n de logging
logging.basicConfig(
    level=getattr(logging, settings.monitoring.log_level.upper()),
    format=settings.monitoring.log_format
)
log = logging.getLogger("aqxion")

# Cache local para rate limiting
domain_last_request: Dict[str, float] = {}
domain_error_count: Dict[str, int] = {}
domain_backoff_until: Dict[str, float] = {}

# Sistema de caché multinivel (reemplaza el caché local anterior)
# content_cache = TTLCache(maxsize=settings.cache.local_cache_size, ttl=settings.cache.local_cache_ttl)


@dataclass
class ScrapedPost:
    """Estructura de datos para posts scrapeados"""
    id: str
    source: str
    url: str
    created_at: str
    keyword: str
    tag: str
    title: Optional[str] = None
    body: Optional[str] = None
    lang: str = "es"
    published_at: Optional[str] = None
    relevance_score: int = 0

    def to_dict(self) -> Dict:
        """Convertir a diccionario para base de datos"""
        return asdict(self)


class TokenBucketRateLimiter:
    """Rate limiter avanzado con token bucket y jitter"""

    def __init__(self):
        self.domain_tokens = {}  # tokens disponibles por dominio
        self.domain_last_refill = {}  # último refill por dominio
        self.domain_burst_capacity = {}  # capacidad máxima por dominio
        self.domain_refill_rate = {}  # tokens por segundo por dominio

        # Configuraciones por defecto
        self.default_burst_capacity = 10  # máximo 10 requests en burst
        self.default_refill_rate = 2.0  # 2 tokens por segundo
        self.jitter_range = (0.1, 0.5)  # jitter entre 0.1s y 0.5s

        # Overrides para dominios sensibles
        self.sensitive_domains = {
            'google.com': {'burst': 3, 'rate': 0.5},
            'bing.com': {'burst': 3, 'rate': 0.5},
            'duckduckgo.com': {'burst': 5, 'rate': 1.0},
            'facebook.com': {'burst': 2, 'rate': 0.3},
            'twitter.com': {'burst': 3, 'rate': 0.5},
            'linkedin.com': {'burst': 2, 'rate': 0.3},
        }

    def _get_domain_config(self, domain: str) -> Dict[str, float]:
        """Obtener configuración específica para un dominio"""
        if domain in self.sensitive_domains:
            config = self.sensitive_domains[domain]
            return {
                'burst': config['burst'],
                'rate': config['rate']
            }
        return {
            'burst': self.default_burst_capacity,
            'rate': self.default_refill_rate
        }

    def _refill_tokens(self, domain: str) -> None:
        """Refill tokens para un dominio"""
        now = asyncio.get_event_loop().time()
        config = self._get_domain_config(domain)

        if domain not in self.domain_last_refill:
            # Primera vez - inicializar con capacidad máxima
            self.domain_tokens[domain] = config['burst']
            self.domain_burst_capacity[domain] = config['burst']
            self.domain_refill_rate[domain] = config['rate']
            self.domain_last_refill[domain] = now
            return

        # Calcular tokens a agregar
        time_passed = now - self.domain_last_refill[domain]
        tokens_to_add = time_passed * config['rate']

        if tokens_to_add > 0:
            current_tokens = self.domain_tokens.get(domain, 0)
            max_tokens = self.domain_burst_capacity.get(domain, config['burst'])

            self.domain_tokens[domain] = min(current_tokens + tokens_to_add, max_tokens)
            self.domain_last_refill[domain] = now

    async def wait_if_needed(self, domain: str) -> None:
        """Esperar si es necesario según token bucket con jitter"""
        self._refill_tokens(domain)

        config = self._get_domain_config(domain)
        current_tokens = self.domain_tokens.get(domain, config['burst'])

        if current_tokens >= 1:
            # Hay tokens disponibles - consumir uno
            self.domain_tokens[domain] = current_tokens - 1

            # Aplicar jitter para evitar patrones predecibles
            import random
            jitter = random.uniform(*self.jitter_range)
            await asyncio.sleep(jitter)
            return

        # No hay tokens - calcular tiempo de espera
        time_to_next_token = 1.0 / config['rate']
        wait_time = time_to_next_token + random.uniform(*self.jitter_range)

        log.debug(f"Rate limiting: esperando {wait_time:.2f}s para {domain} (tokens: {current_tokens:.1f})")
        await asyncio.sleep(wait_time)

        # Después de esperar, consumir el token
        self._refill_tokens(domain)
        if self.domain_tokens.get(domain, 0) > 0:
            self.domain_tokens[domain] -= 1


class AsyncRateLimiter:
    """Rate limiter asíncrono inteligente con backoff y token bucket"""

    def __init__(self):
        self.token_bucket = TokenBucketRateLimiter()
        self.domain_last_request = domain_last_request
        self.domain_error_count = domain_error_count
        self.domain_backoff_until = domain_backoff_until

    async def wait_if_needed(self, domain: str) -> None:
        """Esperar si es necesario según rate limiting inteligente"""
        now = asyncio.get_event_loop().time()

        # Verificar backoff activo
        if domain in self.domain_backoff_until and now < self.domain_backoff_until[domain]:
            remaining = self.domain_backoff_until[domain] - now
            log.warning(f"Backoff activo para {domain}, esperando {remaining:.1f}s")
            await asyncio.sleep(min(remaining, scraping_config.max_backoff_delay))
            return

        # Usar token bucket para rate limiting normal
        await self.token_bucket.wait_if_needed(domain)

        self.domain_last_request[domain] = now

    def handle_error(self, domain: str, error: Exception) -> None:
        """Manejar errores y aplicar backoff"""
        error_count = self.domain_error_count.get(domain, 0) + 1
        self.domain_error_count[domain] = error_count

        # Calcular backoff segÃºn tipo de error
        if isinstance(error, aiohttp.ClientResponseError):
            status_code = error.status
            if status_code == 429:
                backoff_seconds = min(60 * (2 ** error_count), 300)
                self.domain_backoff_until[domain] = asyncio.get_event_loop().time() + backoff_seconds
                log.warning(f"Rate limit hit {domain} (429), backoff {backoff_seconds}s")
            elif status_code >= 500:
                backoff_seconds = min(30 * (2 ** error_count), 120)
                self.domain_backoff_until[domain] = asyncio.get_event_loop().time() + backoff_seconds
                log.warning(f"Server error {status_code} {domain}, backoff {backoff_seconds}s")
            elif status_code == 403:
                backoff_seconds = min(300 * (2 ** error_count), 1800)
                self.domain_backoff_until[domain] = asyncio.get_event_loop().time() + backoff_seconds
                log.warning(f"Access forbidden {status_code} {domain}, backoff {backoff_seconds}s")
        else:
            # Error de conexiÃ³n o timeout
            backoff_seconds = min(5 * (2 ** error_count), 30)
            self.domain_backoff_until[domain] = asyncio.get_event_loop().time() + backoff_seconds
            log.warning(f"Connection error {domain}, backoff {backoff_seconds}s")

    def reset_error_count(self, domain: str) -> None:
        """Resetear contador de errores en caso de Ã©xito"""
        if domain in self.domain_error_count:
            self.domain_error_count[domain] = 0
        if domain in self.domain_backoff_until:
            del self.domain_backoff_until[domain]


class AsyncScraper:
    """Scraper completamente asÃ­ncrono con arquitectura moderna"""

    def __init__(self):
        self.rate_limiter = AsyncRateLimiter()
        self.session: Optional[ClientSession] = None
        self.alert_system = AlertSystem()
        self.cache_manager = cache_manager

    async def __aenter__(self):
        """Inicializar recursos asÃ­ncronos"""
        # Configurar connector con lÃ­mites
        connector = TCPConnector(
            limit=scraping_config.max_concurrent_requests,
            limit_per_host=scraping_config.max_concurrent_requests // 2
        )

        # Configurar timeout
        timeout = ClientTimeout(total=30, connect=10)

        # Crear sesiÃ³n
        self.session = ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Liberar recursos"""
        if self.session:
            await self.session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def fetch_url(self, url: str) -> Optional[str]:
        """Obtener contenido de URL con retry automático y caché inteligente"""
        domain = urlparse(url).netloc

        # 1. Verificar caché antes de hacer petición
        try:
            cached_content = await cache_manager.get_cached_url_content(url)
            if cached_content is not None:
                log.debug(f"Cache hit for URL: {url}")
                return cached_content
        except Exception as e:
            log.warning(f"Error checking cache for {url}: {e}")

        # 2. Aplicar rate limiting
        await self.rate_limiter.wait_if_needed(domain)

        try:
            if not self.session:
                raise RuntimeError("HTTP session not initialized")

            async with self.session.get(url) as response:
                response.raise_for_status()
                content = await response.text()

                # Resetear errores en caso de éxito
                self.rate_limiter.reset_error_count(domain)

                # 3. Cachear el contenido obtenido
                try:
                    await cache_manager.set_cached_url_content(url, content)
                    log.debug(f"Cached content for URL: {url}")
                except Exception as e:
                    log.warning(f"Error caching content for {url}: {e}")

                return content

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            log.warning(f"Error fetching {url}: {e}")
            self.rate_limiter.handle_error(domain, e)
            raise  # Re-raise para que tenacity maneje el retry

    def should_scrape_detail(self, url: str, title: str, keyword: str) -> Tuple[bool, str]:
        """Filtrado avanzado antes de hacer request detallada"""
        # Filtros de tÃ­tulo
        if len(title.strip()) < scraping_config.min_title_length:
            return False, "tÃ­tulo demasiado corto"

        # Filtros de URL
        url_lower = url.lower()
        irrelevant_patterns = [
            '/tag/', '/category/', '/author/', '/archive/', '/page/',
            '/search', '/feed', '/rss', '/comments', '/reply',
            '/login', '/register', '/admin', '/wp-admin', '/wp-login',
            '/user', '/profile', '/account', '/settings'
        ]

        if any(pattern in url_lower for pattern in irrelevant_patterns):
            return False, "patrÃ³n URL irrelevante"

        # Verificar relaciÃ³n con keyword
        keyword_lower = keyword.lower()
        title_words = set(title.lower().split())
        keyword_words = set(keyword_lower.split())

        if not keyword_words.intersection(title_words) and keyword_lower not in title.lower():
            return False, "tÃ­tulo no relacionado con keyword"

        return True, "vÃ¡lido para scraping"

    def validate_content_quality(self, title: str, body: Optional[str]) -> Tuple[bool, str]:
        """Validar calidad del contenido"""
        if len(title.strip()) < scraping_config.min_title_length:
            return False, "tÃ­tulo demasiado corto"

        if body and len(body.strip()) < scraping_config.min_content_length:
            return False, "contenido demasiado corto"

        # Detectar spam con filtros más inteligentes
        spam_patterns = [
            r'\b(?:viagra|casino|lottery|winner|prize)\b',
            r'(?:http|https|www\.)\S{50,}',
            r'\b\d{10,}\b',
            r'[A-Z]{10,}',  # Solo detectar más de 10 mayúsculas consecutivas (spam real)
            r'(.)\1{4,}',   # Caracteres repetidos
        ]

        # Aplicar patrones de spam al texto original (no lowercased)
        full_text = f"{title} {body or ''}"
        for pattern in spam_patterns:
            if re.search(pattern, full_text):
                return False, f"patrÃ³n de spam detectado: {pattern}"

        # Para otros checks, usar texto en minúsculas
        text_to_check = full_text.lower()

        # Verificar que no sea texto completamente en mayúsculas (excepto títulos cortos)
        if len(full_text) > 50:  # Solo verificar para textos largos
            uppercase_ratio = sum(1 for c in full_text if c.isupper()) / len(full_text)
            if uppercase_ratio > 0.8:  # Más del 80% en mayúsculas
                return False, "texto mayoritariamente en mayúsculas"

        # Verificar palabras reales
        words = re.findall(r'\b\w{3,}\b', text_to_check)
        if len(words) < 3:
            return False, "contenido insuficiente"

        return True, "contenido vÃ¡lido"

    def calculate_relevance_score(self, tag: str, title: str, body: Optional[str]) -> int:
        """Calcular score de relevancia"""
        base_score = {'dolor': 100, 'busqueda': 75, 'objecion': 50}.get(tag, 10)

        bonus = 0

        # Longitud del tÃ­tulo
        if len(title.strip()) > 50:
            bonus += 10
        elif len(title.strip()) > 30:
            bonus += 5

        # Longitud del contenido
        if body:
            if len(body.strip()) > 200:
                bonus += 15
            elif len(body.strip()) > 100:
                bonus += 10
            elif len(body.strip()) > 50:
                bonus += 5

        # Palabras de urgencia
        urgent_words = ['urgente', 'inmediato', 'ya', 'necesito', 'ayuda', 'problema']
        text = f"{title} {body or ''}".lower()
        bonus += sum(1 for word in urgent_words if word in text) * 5

        return min(base_score + bonus, 150)

    def is_duplicate_post(self, title: str, body: Optional[str], url: str, keyword: str) -> bool:
        """Verificar duplicados usando cache multinivel y base de datos"""
        # Verificar en caché de URLs procesadas
        cache_key = f"processed_url:{hashlib.md5(url.encode()).hexdigest()}"
        try:
            # Usar versión síncrona para compatibilidad
            from cache_system import get_cached_url_content_sync
            cached_url = get_cached_url_content_sync(url)
            if cached_url is not None:
                return True
        except Exception:
            pass

        # Marcar URL como procesada en caché
        try:
            from cache_system import set_cached_url_content_sync
            set_cached_url_content_sync(url, "processed", 3600)  # 1 hora
        except Exception:
            pass

        return False

    async def is_content_duplicate(self, content: str) -> Tuple[bool, Optional[str]]:
        """Verificar si el contenido ya fue procesado usando hash de contenido"""
        try:
            existing_post_id = await self.cache_manager.get_cached_content_hash(content)
            if existing_post_id:
                log.debug(f"Content duplicate detected: {existing_post_id}")
                return True, existing_post_id
        except Exception as e:
            log.warning(f"Error checking content duplicate: {e}")

        return False, None

    async def cache_content_hash(self, content: str, post_id: str) -> bool:
        """Cachear hash de contenido para futura deduplicación"""
        try:
            success = await self.cache_manager.set_cached_content_hash(content, post_id)
            if success:
                log.debug(f"Cached content hash for post: {post_id}")
            return success
        except Exception as e:
            log.warning(f"Error caching content hash: {e}")
            return False

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema de caché"""
        try:
            return self.cache_manager.get_stats()
        except Exception as e:
            log.warning(f"Error getting cache stats: {e}")
            return {}

    async def clear_cache(self, cache_type: str = 'all') -> bool:
        """Limpiar caché específica o todas las cachés"""
        try:
            if cache_type == 'all':
                return await self.cache_manager.cache.clear()
            elif cache_type == 'url':
                return await self.cache_manager.url_cache.clear()
            elif cache_type == 'content':
                return await self.cache_manager.content_cache.clear()
            elif cache_type == 'intent':
                return await self.cache_manager.intent_cache.clear()
            else:
                return False
        except Exception as e:
            log.warning(f"Error clearing cache: {e}")
            return False

    async def scrape_single_url(self, url: str, keyword: str) -> Optional[ScrapedPost]:
        """Scrape una URL individual usando Scrapling"""
        try:
            log.info(f"🔍 Scraping with Scrapling: {url}")

            # Usar Scrapling para scraping mejorado
            result = scrapling_scraper.scrape_url(url)

            if result['status'] != 'success':
                log.warning(f"Scrapling scrape failed for {url}: {result.get('error', 'Unknown error')}")
                return None

            # Extraer información del resultado de Scrapling
            title = result.get('title', '')
            if not title:
                log.debug(f"No title found for {url}")
                return None

            # Usar el texto completo como body
            body = result.get('full_text', '')
            if not body:
                # Fallback: usar el primer texto encontrado
                texts = result.get('texts_found', [])
                if texts > 0:
                    body = "Contenido encontrado pero no clasificado"
                else:
                    body = ""

            # Limpiar y truncar body
            if body:
                body = " ".join(body.split())[:600]

            # Verificar duplicados de contenido usando hash
            content_text = f"{title} {body or ''}".strip()
            if content_text:
                is_duplicate, existing_id = await self.is_content_duplicate(content_text)
                if is_duplicate:
                    log.debug(f"Contenido duplicado detectado: {existing_id}")
                    return None

            # Usar la mejor clasificación de Scrapling
            classifications = result.get('classifications', [])
            if classifications:
                # Usar la clasificación con mayor confianza
                best_classification = max(classifications, key=lambda x: x.get('confidence', 0))
                tag = best_classification['tag']
            else:
                # Fallback a clasificación tradicional usando el contenido completo
                full_content = result.get('full_text', '')
                if full_content:
                    tag = tag_item(full_content)
                else:
                    tag = tag_item(content_text)

            # Si aún es ruido pero tenemos contenido válido, intentar clasificar mejor
            if tag == 'ruido' and body and len(body) > 20:
                # Buscar patrones específicos en el contenido
                body_lower = body.lower()
                if any(word in body_lower for word in ['problema', 'error', 'urgente', 'necesito', 'busco']):
                    tag = 'dolor' if 'problema' in body_lower or 'error' in body_lower else 'busqueda'

            # Validar calidad
            is_valid, reason = self.validate_content_quality(title, body)
            if not is_valid:
                log.debug(f"Contenido rechazado: {reason}")
                return None

            # Verificar duplicados
            if self.is_duplicate_post(title, body, url, keyword):
                log.debug(f"Post duplicado: {title[:50]}...")
                return None

            # Calcular score basado en clasificaciones
            relevance_score = self.calculate_relevance_score(tag, title, body)
            if classifications:
                # Bonus por clasificaciones encontradas
                relevance_score += len(classifications) * 5

            # Crear post
            post = ScrapedPost(
                id=hashlib.sha256(f"{url}{title}".encode()).hexdigest()[:16],
                source=urlparse(url).netloc,
                url=url,
                title=title[:300],
                body=body,
                created_at=dt.datetime.utcnow().isoformat(),
                keyword=keyword,
                tag=tag,
                published_at=None,  # Scrapling no extrae fechas por ahora
                relevance_score=relevance_score
            )

            # Cachear hash de contenido para futura deduplicación
            if content_text:
                await self.cache_content_hash(content_text, post.id)

            log.info(f"✅ Scrapling scrape successful: {url} (tag: {tag}, score: {relevance_score})")
            return post

        except Exception as e:
            log.warning(f"Error procesando {url} con Scrapling: {e}")
            return None

    async def scrape_keyword(self, keyword: str) -> List[ScrapedPost]:
        """Scrape todas las URLs para una keyword"""
        log.info(f"ðŸ” Scrapeando keyword: {keyword}")

        # Obtener URLs de búsqueda
        urls = await search_urls_for(keyword)
        if not urls:
            log.warning(f"No se encontraron URLs para {keyword}")
            return []

        log.info(f"ðŸ“‹ Encontradas {len(urls)} URLs para {keyword}")

        # Procesar URLs concurrentemente
        tasks = []
        for url in urls[:scraping_config.max_per_keyword]:
            # Filtrado bÃ¡sico antes de scraping
            try:
                content = await self.fetch_url(url)
                if content:
                    log.debug(f"Contenido obtenido de {url}: {len(content)} caracteres")
                    html = HTMLParser(content)
                    title_elem = html.css_first("title")
                    if title_elem:
                        title = title_elem.text().strip()
                        log.debug(f"Título encontrado: {title}")
                        should_scrape, reason = self.should_scrape_detail(url, title, keyword)
                        if should_scrape:
                            tasks.append(self.scrape_single_url(url, keyword))
                        else:
                            log.debug(f"Saltando {url}: {reason}")
                    else:
                        log.debug(f"No se encontró título en {url}")
                else:
                    log.debug(f"No se pudo obtener contenido de {url}")
            except Exception as e:
                log.debug(f"Error en filtrado de {url}: {e}")

        # Ejecutar scraping concurrente
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            posts = [r for r in results if isinstance(r, ScrapedPost)]
            log.info(f"âœ… Procesados {len(posts)} posts vÃ¡lidos para {keyword}")
            return posts

        return []

    async def save_posts(self, posts: List[ScrapedPost]) -> None:
        """Guardar posts en base de datos"""
        if not posts:
            return

        # Guardar en lotes para mejor rendimiento
        batch_size = 50
        for i in range(0, len(posts), batch_size):
            batch = posts[i:i + batch_size]
            for post in batch:
                try:
                    upsert_post(post.to_dict())

                    # Alertas para leads de alto valor
                    if (post.tag in ['dolor', 'busqueda'] and
                        post.relevance_score >= scraping_config.high_value_threshold):
                        alert_lead(
                            title=post.title or "",
                            body=post.body or "",
                            url=post.url,
                            keyword=post.keyword,
                            tag=post.tag,
                            score=post.relevance_score
                        )

                except Exception as e:
                    log.error(f"Error guardando post {post.id}: {e}")

        log.info(f"ðŸ’¾ Guardados {len(posts)} posts en base de datos")

    async def run_scraping_cycle(self) -> None:
        """Ejecutar un ciclo completo de scraping"""
        log.info("ðŸš€ Iniciando ciclo de scraping asÃ­ncrono")

        # Inicializar base de datos
        init_db()

        # Configurar alertas
        auto_configure_alerts()
        alert_system_status("started", "Iniciando scraping asÃ­ncrono")

        total_posts = 0

        # Procesar keywords secuencialmente para mejor control
        for keyword in scraping_config.keywords:
            try:
                posts = await self.scrape_keyword(keyword)
                if posts:
                    await self.save_posts(posts)
                    total_posts += len(posts)

                # PequeÃ±a pausa entre keywords para no sobrecargar
                await asyncio.sleep(1)

            except Exception as e:
                log.error(f"Error procesando keyword {keyword}: {e}")

        log.info(f"âœ… Ciclo de scraping completado. Total posts: {total_posts}")
        alert_system_status("completed", f"Ciclo completado: {total_posts} posts procesados")


async def main():
    """Punto de entrada principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Aqxion Scraper con Scrapling')
    parser.add_argument('--single-url', help='Scrape una URL específica')
    parser.add_argument('--keyword', default='marketing digital',
                       help='Keyword para la URL (requerido con --single-url)')
    parser.add_argument('--test-url', help='URL de prueba para testing')

    args = parser.parse_args()

    async with AsyncScraper() as scraper:
        if args.single_url:
            # Modo single URL
            if not args.keyword:
                print("Error: --keyword es requerido cuando se usa --single-url")
                return

            print(f"🔍 Scraping single URL: {args.single_url}")
            print(f"📝 Keyword: {args.keyword}")

            post = await scraper.scrape_single_url(args.single_url, args.keyword)
            if post:
                print("✅ Post creado exitosamente:")
                print(f"   ID: {post.id}")
                print(f"   Title: {post.title}")
                print(f"   Tag: {post.tag}")
                print(f"   Score: {post.relevance_score}")
                print(f"   Body: {post.body[:100]}..." if post.body else "   Body: None")

                # Guardar el post
                await scraper.save_posts([post])
                print("💾 Post guardado en base de datos")
            else:
                print("❌ No se pudo crear post válido")

        elif args.test_url:
            # Modo test URL (similar a single URL pero sin guardar)
            keyword = args.keyword or 'test'
            print(f"🧪 Testing URL: {args.test_url}")
            print(f"📝 Keyword: {keyword}")

            post = await scraper.scrape_single_url(args.test_url, keyword)
            if post:
                print("✅ Test exitoso - Post creado:")
                print(f"   Title: {post.title}")
                print(f"   Tag: {post.tag}")
                print(f"   Score: {post.relevance_score}")
                print(f"   Content Length: {len(post.body or '')}")
            else:
                print("❌ Test fallido - No se pudo crear post")
                # Debug: intentar scrapear manualmente para ver qué pasa
                print("🔍 Debug: Intentando scraping manual...")
                try:
                    result = scrapling_scraper.scrape_url(args.test_url)
                    print(f"   Scrapling Status: {result.get('status')}")
                    print(f"   Title: {result.get('title', 'N/A')}")
                    print(f"   Content Length: {result.get('content_length', 0)}")
                    print(f"   Texts Found: {result.get('texts_found', 0)}")
                    print(f"   Classifications: {result.get('classification_count', 0)}")

                    if result.get('status') == 'success':
                        title = result.get('title', '')
                        body = result.get('full_text', '')
                        print(f"   Body Preview: {body[:100] if body else 'Empty'}...")

                        # Probar validación de calidad
                        is_valid, reason = scraper.validate_content_quality(title, body)
                        print(f"   Quality Check: {'✅ PASS' if is_valid else '❌ FAIL'} - {reason}")

                        if is_valid:
                            tag = tag_item(body or title)
                            print(f"   Tag: {tag}")
                            if tag == 'ruido':
                                print("   ⚠️ Tag is 'ruido' - content may not match classification patterns")

                except Exception as e:
                    print(f"   Debug Error: {e}")

        else:
            # Modo normal - ciclo completo
            await scraper.run_scraping_cycle()

if (__name__ == '__main__'):
    # Ejecutar scraper asíncrono
    asyncio.run(main())
