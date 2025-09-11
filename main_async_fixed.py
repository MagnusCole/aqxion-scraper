"""
Aqxion Scraper v2.0 - Arquitectura completamente asíncrona
Reemplaza la implementación híbrida síncrona/asíncrona con un sistema consistente
"""

import asyncio
import hashlib
import datetime as dt
import re
import logging
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
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

# Configuración
settings = get_settings()
scraping_config = settings.scraping
db_config = settings.database

# Configuración de logging
logging.basicConfig(
    level=getattr(logging, settings.monitoring.log_level.upper()),
    format=settings.monitoring.log_format
)
log = logging.getLogger("aqxion")

# Cache local para rate limiting
domain_last_request: Dict[str, float] = {}
domain_error_count: Dict[str, int] = {}
domain_backoff_until: Dict[str, float] = {}

# Cache para URLs procesadas
url_cache: Set[str] = set()
content_cache = TTLCache(maxsize=settings.cache.local_cache_size, ttl=settings.cache.local_cache_ttl)


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


class AsyncRateLimiter:
    """Rate limiter asíncrono inteligente con backoff"""

    def __init__(self):
        self.domain_last_request = domain_last_request
        self.domain_error_count = domain_error_count
        self.domain_backoff_until = domain_backoff_until

    async def wait_if_needed(self, domain: str) -> None:
        """Esperar si es necesario según rate limiting"""
        now = asyncio.get_event_loop().time()

        # Verificar backoff activo
        if domain in self.domain_backoff_until and now < self.domain_backoff_until[domain]:
            remaining = self.domain_backoff_until[domain] - now
            log.warning(f"Backoff activo para {domain}, esperando {remaining:.1f}s")
            await asyncio.sleep(min(remaining, scraping_config.max_backoff_delay))
            return

        # Rate limiting normal
        if domain in self.domain_last_request:
            time_since_last = now - self.domain_last_request[domain]
            base_delay = scraping_config.domain_rate_limit

            # Aplicar backoff adicional por errores
            error_count = self.domain_error_count.get(domain, 0)
            if error_count > 0:
                backoff_delay = min(
                    base_delay * (2 ** error_count),
                    scraping_config.max_backoff_delay
                )
                base_delay = backoff_delay

            if time_since_last < base_delay:
                actual_delay = base_delay - time_since_last
                log.debug(f"Rate limiting: esperando {actual_delay:.2f}s para {domain}")
                await asyncio.sleep(actual_delay)

        self.domain_last_request[domain] = now

    def handle_error(self, domain: str, error: Exception) -> None:
        """Manejar errores y aplicar backoff"""
        error_count = self.domain_error_count.get(domain, 0) + 1
        self.domain_error_count[domain] = error_count

        # Calcular backoff según tipo de error
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
            # Error de conexión o timeout
            backoff_seconds = min(5 * (2 ** error_count), 30)
            self.domain_backoff_until[domain] = asyncio.get_event_loop().time() + backoff_seconds
            log.warning(f"Connection error {domain}, backoff {backoff_seconds}s")

    def reset_error_count(self, domain: str) -> None:
        """Resetear contador de errores en caso de éxito"""
        if domain in self.domain_error_count:
            self.domain_error_count[domain] = 0
        if domain in self.domain_backoff_until:
            del self.domain_backoff_until[domain]


class AsyncScraper:
    """Scraper completamente asíncrono con arquitectura moderna"""

    def __init__(self):
        self.rate_limiter = AsyncRateLimiter()
        self.session: Optional[ClientSession] = None
        self.alert_system = AlertSystem()

    async def __aenter__(self):
        """Inicializar recursos asíncronos"""
        # Configurar connector con límites
        connector = TCPConnector(
            limit=scraping_config.max_concurrent_requests,
            limit_per_host=scraping_config.max_concurrent_requests // 2
        )

        # Configurar timeout
        timeout = ClientTimeout(total=30, connect=10)

        # Crear sesión
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
        """Obtener contenido de URL con retry automático"""
        domain = urlparse(url).netloc

        # Aplicar rate limiting
        await self.rate_limiter.wait_if_needed(domain)

        try:
            if not self.session:
                raise RuntimeError("HTTP session not initialized")

            async with self.session.get(url) as response:
                response.raise_for_status()
                content = await response.text()

                # Resetear errores en caso de éxito
                self.rate_limiter.reset_error_count(domain)

                return content

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            log.warning(f"Error fetching {url}: {e}")
            self.rate_limiter.handle_error(domain, e)
            raise  # Re-raise para que tenacity maneje el retry

    def should_scrape_detail(self, url: str, title: str, keyword: str) -> Tuple[bool, str]:
        """Filtrado avanzado antes de hacer request detallada"""
        # Filtros de título
        if len(title.strip()) < scraping_config.min_title_length:
            return False, "título demasiado corto"

        # Filtros de URL
        url_lower = url.lower()
        irrelevant_patterns = [
            '/tag/', '/category/', '/author/', '/archive/', '/page/',
            '/search', '/feed', '/rss', '/comments', '/reply',
            '/login', '/register', '/admin', '/wp-admin', '/wp-login',
            '/user', '/profile', '/account', '/settings'
        ]

        if any(pattern in url_lower for pattern in irrelevant_patterns):
            return False, "patrón URL irrelevante"

        # Verificar relación con keyword
        keyword_lower = keyword.lower()
        title_words = set(title.lower().split())
        keyword_words = set(keyword_lower.split())

        if not keyword_words.intersection(title_words) and keyword_lower not in title.lower():
            return False, "título no relacionado con keyword"

        return True, "válido para scraping"

    def validate_content_quality(self, title: str, body: Optional[str]) -> Tuple[bool, str]:
        """Validar calidad del contenido"""
        if len(title.strip()) < scraping_config.min_title_length:
            return False, "título demasiado corto"

        if body and len(body.strip()) < scraping_config.min_content_length:
            return False, "contenido demasiado corto"

        # Detectar spam
        spam_patterns = [
            r'\b(?:viagra|casino|lottery|winner|prize)\b',
            r'(?:http|https|www\.)\S{50,}',
            r'\b\d{10,}\b',
            r'[A-Z]{5,}',
            r'(.)\1{4,}',
        ]

        text_to_check = f"{title} {body or ''}".lower()
        for pattern in spam_patterns:
            if re.search(pattern, text_to_check, re.IGNORECASE):
                return False, f"patrón de spam detectado: {pattern}"

        # Verificar palabras reales
        words = re.findall(r'\b\w{3,}\b', text_to_check)
        if len(words) < 3:
            return False, "contenido insuficiente"

        return True, "contenido válido"

    def calculate_relevance_score(self, tag: str, title: str, body: Optional[str]) -> int:
        """Calcular score de relevancia"""
        base_score = {'dolor': 100, 'busqueda': 75, 'objecion': 50}.get(tag, 10)

        bonus = 0

        # Longitud del título
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
        """Verificar duplicados usando cache y base de datos"""
        # Cache rápido de URLs
        if url in url_cache:
            return True

        # Aquí iría la lógica de deduplicación con base de datos
        # Por ahora, solo verificamos URL en cache
        url_cache.add(url)
        return False

    async def scrape_single_url(self, url: str, keyword: str) -> Optional[ScrapedPost]:
        """Scrape una URL individual"""
        try:
            # Obtener contenido
            content = await self.fetch_url(url)
            if not content:
                return None

            # Parsear HTML
            html = HTMLParser(content)

            # Extraer información básica
            title_elem = html.css_first("title")
            title = title_elem.text() if title_elem else ""

            if not title:
                return None

            # Extraer body/snippet
            body_selectors = [
                "meta[name='description']",
                "meta[property='og:description']",
                "[class*='content']",
                "[class*='post']",
                "article",
                "main"
            ]

            body = None
            for selector in body_selectors:
                elem = html.css_first(selector)
                if elem:
                    if selector.startswith("meta"):
                        body = elem.attributes.get("content", "")
                    else:
                        body = elem.text()
                    if body and len(body.strip()) > 50:
                        break

            # Limpiar y truncar body
            if body:
                body = " ".join(body.split())[:600]

            # Extraer fecha de publicación
            published_at = None
            date_selectors = [
                "meta[property='article:published_time']",
                "time[datetime]",
                "[class*='date']",
                "[class*='published']"
            ]

            for selector in date_selectors:
                elem = html.css_first(selector)
                if elem:
                    if selector.startswith("meta"):
                        published_at = elem.attributes.get("content")
                    elif selector == "time[datetime]":
                        published_at = elem.attributes.get("datetime")
                    else:
                        published_at = elem.text()
                    if published_at:
                        break

            # Etiquetado de intención
            text_for_tag = f"{title} {body or ''}"
            tag = tag_item(text_for_tag)

            # Validar calidad
            is_valid, reason = self.validate_content_quality(title, body)
            if not is_valid:
                log.debug(f"Contenido rechazado: {reason}")
                return None

            # Verificar duplicados
            if self.is_duplicate_post(title, body, url, keyword):
                log.debug(f"Post duplicado: {title[:50]}...")
                return None

            # Calcular score
            relevance_score = self.calculate_relevance_score(tag, title, body)

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
                published_at=published_at,
                relevance_score=relevance_score
            )

            return post

        except Exception as e:
            log.warning(f"Error procesando {url}: {e}")
            return None

    async def scrape_keyword(self, keyword: str) -> List[ScrapedPost]:
        """Scrape todas las URLs para una keyword"""
        log.info(f"🔍 Scrapeando keyword: {keyword}")

        # Obtener URLs de búsqueda
        urls = search_urls_for(keyword)
        if not urls:
            log.warning(f"No se encontraron URLs para {keyword}")
            return []

        log.info(f"📋 Encontradas {len(urls)} URLs para {keyword}")

        # Procesar URLs concurrentemente
        tasks = []
        for url in urls[:scraping_config.max_per_keyword]:
            # Filtrado básico antes de scraping
            try:
                content = await self.fetch_url(url)
                if content:
                    html = HTMLParser(content)
                    title_elem = html.css_first("title")
                    if title_elem:
                        title = title_elem.text().strip()
                        should_scrape, reason = self.should_scrape_detail(url, title, keyword)
                        if should_scrape:
                            tasks.append(self.scrape_single_url(url, keyword))
                        else:
                            log.debug(f"Saltando {url}: {reason}")
            except Exception as e:
                log.debug(f"Error en filtrado de {url}: {e}")

        # Ejecutar scraping concurrente
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            posts = [r for r in results if isinstance(r, ScrapedPost)]
            log.info(f"✅ Procesados {len(posts)} posts válidos para {keyword}")
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

        log.info(f"💾 Guardados {len(posts)} posts en base de datos")

    async def run_scraping_cycle(self) -> None:
        """Ejecutar un ciclo completo de scraping"""
        log.info("🚀 Iniciando ciclo de scraping asíncrono")

        # Inicializar base de datos
        init_db()

        # Configurar alertas
        auto_configure_alerts()
        alert_system_status("started", "Iniciando scraping asíncrono")

        total_posts = 0

        # Procesar keywords secuencialmente para mejor control
        for keyword in scraping_config.keywords:
            try:
                posts = await self.scrape_keyword(keyword)
                if posts:
                    await self.save_posts(posts)
                    total_posts += len(posts)

                # Pequeña pausa entre keywords para no sobrecargar
                await asyncio.sleep(1)

            except Exception as e:
                log.error(f"Error procesando keyword {keyword}: {e}")

        log.info(f"✅ Ciclo de scraping completado. Total posts: {total_posts}")
        alert_system_status("completed", f"Ciclo completado: {total_posts} posts procesados")


async def main():
    """Punto de entrada principal"""
    async with AsyncScraper() as scraper:
        await scraper.run_scraping_cycle()


if __name__ == "__main__":
    # Ejecutar scraper asíncrono
    asyncio.run(main())
<parameter name="filePath">d:\Projects\aqxion-scraper-mvp\main_async.py
