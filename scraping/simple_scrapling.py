"""
Simplified Scrapling Integration for Aqxion Scraper
Basic HTTP scraping without complex dependencies
"""

import aiohttp
from typing import Optional, Dict, Any
from config.config_v2 import get_settings

settings = get_settings()

class SimpleScraplingScraper:
    """Simple scraper using aiohttp"""

    def __init__(self):
        self.session = None

    async def scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape URL content"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        content = await response.text()
                        return {
                            "url": url,
                            "content": content,
                            "status": response.status,
                            "success": True
                        }
                    else:
                        return {
                            "url": url,
                            "content": "",
                            "status": response.status,
                            "success": False
                        }
        except Exception as e:
            return {
                "url": url,
                "content": "",
                "status": 0,
                "success": False,
                "error": str(e)
            }

# Global instance
scrapling_scraper = SimpleScraplingScraper()