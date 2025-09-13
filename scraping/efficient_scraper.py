"""
Efficient Scraper for Aqxion Insights
Focused on fast, reliable scraping with Redis caching
"""

import asyncio
import hashlib
import re
import time
from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from aiohttp import ClientTimeout, ClientSession, TCPConnector
from selectolax.parser import HTMLParser
from cache.redis_cache import redis_cache, init_redis_cache, close_redis_cache
from config.config_v2 import MIN_TITLE_LENGTH

log = logging.getLogger("efficient_scraper")

@dataclass
class ScrapedData:
    """Estructura para datos scrapeados"""
    url: str
    title: str
    content: str
    metadata: Dict[str, Any]
    scraped_at: datetime
    content_hash: str

@dataclass
class ScrapingResult:
    """Resultado del proceso de scraping"""
    url: str
    success: bool
    data: Optional[ScrapedData] = None
    error: Optional[str] = None
    cached: bool = False
    response_time: float = 0.0

class EfficientScraper:
    """Efficient scraper with Redis caching and smart optimizations"""

    def __init__(self, max_concurrent: int = 10, cache_ttl: int = 3600):
        self.max_concurrent = max_concurrent
        self.cache_ttl = cache_ttl
        self.session: Optional[ClientSession] = None

        # Rate limiting
        self.request_delay = 1.0  # seconds between requests
        self.last_request_time = 0

        # Content filters
        self.min_content_length = 100
        self.max_content_length = 50000

        # User agents rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

    async def __aenter__(self):
        """Initialize scraper resources"""
        await init_redis_cache()

        # Create optimized session
        connector = TCPConnector(
            limit=self.max_concurrent,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True
        )

        timeout = ClientTimeout(total=MIN_TITLE_LENGTH, connect=10)

        self.session = ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )

        log.info(f"🚀 Efficient Scraper initialized with {self.max_concurrent} concurrent connections")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup scraper resources"""
        if self.session:
            await self.session.close()
        await close_redis_cache()

    def _get_cache_key(self, url: str) -> str:
        """Generate cache key for URL"""
        return hashlib.md5(url.encode()).hexdigest()

    def _extract_title(self, html: str) -> str:
        """Extract title from HTML"""
        try:
            parser = HTMLParser(html)
            title_tag = parser.css_first('title')
            if title_tag:
                return title_tag.text().strip()
        except Exception:
            pass
        return "Sin título"

    def _extract_main_content(self, html: str) -> str:
        """Extract main content from HTML"""
        try:
            parser = HTMLParser(html)

            # Remove script and style elements
            for tag in parser.css('script, style, nav, header, footer, aside'):
                tag.decompose()

            # Try to find main content areas
            content_selectors = [
                'main',
                'article',
                '[role="main"]',
                '.content',
                '.main-content',
                '#content',
                '#main',
                'body'
            ]

            for selector in content_selectors:
                content_elem = parser.css_first(selector)
                if content_elem:
                    text = content_elem.text()
                    if len(text.strip()) > self.min_content_length:
                        return text.strip()

            # Fallback to body text
            body = parser.css_first('body')
            if body:
                return body.text().strip()

        except Exception as e:
            log.warning(f"Error extracting content: {e}")

        return ""

    def _calculate_content_hash(self, content: str) -> str:
        """Calculate hash of content for deduplication"""
        return hashlib.md5(content.encode()).hexdigest()

    def _validate_content(self, content: str) -> bool:
        """Validate content quality"""
        if not content or len(content.strip()) < self.min_content_length:
            return False

        if len(content) > self.max_content_length:
            return False

        # Check for meaningful content (not just navigation/scripts)
        words = re.findall(r'\b\w+\b', content.lower())
        if len(words) < 20:  # Too few words
            return False

        # Check for excessive repetition (spam indicator)
        word_counts = {}
        for word in words:
            if len(word) > 3:  # Only count meaningful words
                word_counts[word] = word_counts.get(word, 0) + 1

        max_repetitions = max(word_counts.values()) if word_counts else 0
        if max_repetitions > len(words) * 0.3:  # More than MIN_TITLE_LENGTH% repetition
            return False

        return True

    async def _rate_limit_wait(self):
        """Apply rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last)

        self.last_request_time = time.time()

    async def scrape_single_url(self, url: str) -> ScrapingResult:
        """Scrape a single URL efficiently"""
        start_time = time.time()

        # Ensure session is initialized
        if not self.session:
            return ScrapingResult(
                url=url,
                success=False,
                error="Scraper session not initialized. Use 'async with scraper:' context manager.",
                response_time=time.time() - start_time
            )

        try:
            # Check cache first
            cache_key = self._get_cache_key(url)
            cached_data = await redis_cache.get(cache_key, namespace="scraped_content")

            if cached_data and isinstance(cached_data, dict):
                log.debug(f"✅ Cache hit for: {url}")
                # Convert cached dict to ScrapedData object
                cached_scraped_data = ScrapedData(
                    url=cached_data.get('url', url),
                    title=cached_data.get('title', ''),
                    content=cached_data.get('content', ''),
                    metadata=cached_data.get('metadata', {}),
                    scraped_at=cached_data.get('scraped_at', datetime.now()),
                    content_hash=cached_data.get('content_hash', '')
                )
                return ScrapingResult(
                    url=url,
                    success=True,
                    data=cached_scraped_data,
                    cached=True,
                    response_time=time.time() - start_time
                )

            # Apply rate limiting
            await self._rate_limit_wait()

            # Rotate user agent
            headers = {'User-Agent': self.user_agents[hash(url) % len(self.user_agents)]}

            # Make request
            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    return ScrapingResult(
                        url=url,
                        success=False,
                        error=f"HTTP {response.status}",
                        response_time=time.time() - start_time
                    )

                html = await response.text()

                # Extract data
                title = self._extract_title(html)
                content = self._extract_main_content(html)

                # Validate content
                if not self._validate_content(content):
                    return ScrapingResult(
                        url=url,
                        success=False,
                        error="Content validation failed",
                        response_time=time.time() - start_time
                    )

                # Create scraped data
                content_hash = self._calculate_content_hash(content)
                scraped_data = ScrapedData(
                    url=url,
                    title=title,
                    content=content,
                    metadata={
                        'status_code': response.status,
                        'content_type': response.headers.get('content-type', '') if response.headers else '',
                        'content_length': len(content),
                        'word_count': len(re.findall(r'\b\w+\b', content)),
                    },
                    scraped_at=datetime.now(),
                    content_hash=content_hash
                )

                # Cache the result
                await redis_cache.set(
                    cache_key,
                    scraped_data,
                    ttl=self.cache_ttl,
                    namespace="scraped_content"
                )

                log.info(f"✅ Scraped: {url} ({len(content)} chars)")
                return ScrapingResult(
                    url=url,
                    success=True,
                    data=scraped_data,
                    response_time=time.time() - start_time
                )

        except Exception as e:
            log.error(f"❌ Error scraping {url}: {e}")
            return ScrapingResult(
                url=url,
                success=False,
                error=str(e),
                response_time=time.time() - start_time
            )

    async def scrape_urls_batch(self, urls: List[str], batch_size: int = 5) -> List[ScrapingResult]:
        """Scrape multiple URLs in batches"""
        results = []

        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            log.info(f"📦 Processing batch {i//batch_size + 1}/{(len(urls) + batch_size - 1)//batch_size} ({len(batch)} URLs)")

            # Process batch concurrently
            tasks = [self.scrape_single_url(url) for url in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    results.append(ScrapingResult(
                        url=batch[j],
                        success=False,
                        error=str(result)
                    ))
                else:
                    results.append(result)

            # Small delay between batches
            if i + batch_size < len(urls):
                await asyncio.sleep(0.5)

        return results

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get scraping cache statistics"""
        return await redis_cache.get_stats()

    async def clear_cache(self) -> bool:
        """Clear scraping cache"""
        return await redis_cache.clear_namespace("scraped_content")

# Convenience functions
async def scrape_url(url: str) -> ScrapingResult:
    """Convenience function to scrape a single URL"""
    async with EfficientScraper() as scraper:
        return await scraper.scrape_single_url(url)

async def scrape_urls(urls: List[str], batch_size: int = 5) -> List[ScrapingResult]:
    """Convenience function to scrape multiple URLs"""
    async with EfficientScraper() as scraper:
        return await scraper.scrape_urls_batch(urls, batch_size)