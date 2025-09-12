"""
Scrapling Integration for Aqxion Scraper
Versión simplificada y funcional
"""

import logging
from typing import List, Optional, Dict, Any
import asyncio
from scrapling.fetchers import Fetcher, FetcherSession, StealthyFetcher
from scrapling.parser import Selector

from config_v2 import get_settings
from rules import tag_item

settings = get_settings()
log = logging.getLogger("aqxion-scrapling")

class ScraplingScraper:
    """Scraper usando Scrapling para mejor rendimiento"""

    def __init__(self):
        self.settings = settings.scraping

    def fetch_content(self, url: str) -> Optional[str]:
        """Fetch content usando Scrapling con fallback"""
        try:
            # Intentar fetch normal primero con FetcherSession configurado
            with FetcherSession(
                impersonate='chrome',
                timeout=30,
                retries=2,
                stealthy_headers=True
            ) as session:
                response = session.get(url)

            if response:
                return str(response)
            else:
                log.warning(f"Normal fetch failed for {url}, trying stealth...")

        except Exception as e:
            log.warning(f"Normal fetch error for {url}: {e}")

        # Fallback a stealth fetch usando una función helper síncrona
        try:
            return self._stealth_fetch_sync(url)
        except Exception as e:
            log.error(f"Stealth fetch error for {url}: {e}")

        return None

    def _stealth_fetch_sync(self, url: str) -> Optional[str]:
        """Helper method para stealth fetch síncrono"""
        try:
            # Crear un nuevo event loop si no existe
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Si hay un loop corriendo, necesitamos una solución diferente
                    return None
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Usar StealthyFetcher directamente
            page = StealthyFetcher.fetch(url, headless=True)
            return str(page) if page else None

        except Exception as e:
            log.error(f"Stealth fetch sync error: {e}")
            return None

    def parse_content(self, html: str) -> List[str]:
        """Parse content usando selectores adaptativos"""
        try:
            page = Selector(html)
            results = []

            # Selectores para diferentes tipos de contenido
            selectors = [
                'title',
                'h1', 'h2', 'h3',
                'p',
                '.content', '.post', '.article',
                '.comment', '.review'
            ]

            for selector in selectors:
                try:
                    elements = page.css(selector)
                    for element in elements:
                        text = getattr(element, 'text', '').strip()
                        if text and len(text) > 10:
                            results.append(text)
                except:
                    continue

            return results[:15]  # Limitar resultados

        except Exception as e:
            log.error(f"Parse error: {e}")
            return []

    def classify_content(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Clasifica contenido usando reglas de dolor/búsqueda/objeción"""
        classifications = []

        for text in texts:
            if len(text) > 15:
                tag = tag_item(text)
                if tag != 'ruido':
                    classifications.append({
                        'text': text[:200] + '...' if len(text) > 200 else text,
                        'tag': tag,
                        'confidence': 0.8  # Placeholder
                    })

        # Remover duplicados
        unique = []
        seen = set()
        for c in classifications:
            key = c['text'][:50]
            if key not in seen:
                unique.append(c)
                seen.add(key)

        return unique[:8]  # Top 8

    def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scraping completo de una URL"""
        log.info(f"🔍 Scraping with Scrapling: {url}")

        # Fetch content
        html = self.fetch_content(url)
        if not html:
            return {
                'url': url,
                'status': 'failed',
                'error': 'Could not fetch content'
            }

        # Parse content
        texts = self.parse_content(html)

        # Classify content
        classifications = self.classify_content(texts)

        # Extract title with multiple fallbacks
        title = "Sin título"
        try:
            page = Selector(html)

            # Try title first
            title_elem = page.css_first('title')
            if title_elem and getattr(title_elem, 'text', '').strip():
                title = getattr(title_elem, 'text', '').strip()
            else:
                # Fallback to h1
                h1_elem = page.css_first('h1')
                if h1_elem and getattr(h1_elem, 'text', '').strip():
                    title = getattr(h1_elem, 'text', '').strip()
                else:
                    # Fallback to first meaningful heading
                    for tag in ['h2', 'h3', 'h4']:
                        heading = page.css_first(tag)
                        if heading and getattr(heading, 'text', '').strip():
                            title = getattr(heading, 'text', '').strip()
                            break
        except Exception as e:
            log.warning(f"Error extracting title: {e}")

        # Create full text content
        full_text = ' '.join(texts) if texts else ''

        result = {
            'url': url,
            'status': 'success',
            'title': title,
            'full_text': full_text,
            'content_length': len(full_text),
            'texts_found': len(texts),
            'classifications': classifications,
            'classification_count': len(classifications)
        }

        log.info(f"✅ Scrapling scrape completed: {url} ({len(classifications)} classifications)")
        return result

# Instancia global
scrapling_scraper = ScraplingScraper()

def enhanced_scrape_url(url: str) -> Dict[str, Any]:
    """Función wrapper para usar en el scraper principal"""
    return scrapling_scraper.scrape_url(url)