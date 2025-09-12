"""
Simplified Cache System for Aqxion Scraper
Replaces complex cache_manager with simple TTLCache implementation
"""

from cachetools import TTLCache
from typing import Optional, Dict, Any
import hashlib

class SimpleCacheManager:
    """Simplified cache manager using TTLCache"""

    def __init__(self):
        self.url_cache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour
        self.content_cache = TTLCache(maxsize=500, ttl=1800)  # 30 min
        self.intent_cache = TTLCache(maxsize=2000, ttl=7200)  # 2 hours

    async def get_cached_url_content(self, url: str) -> Optional[str]:
        """Get cached URL content"""
        return self.url_cache.get(url)

    async def set_cached_url_content(self, url: str, content: str) -> bool:
        """Cache URL content"""
        self.url_cache[url] = content
        return True

    async def get_cached_intent_analysis(self, text: str) -> Optional[Dict[str, Any]]:
        """Get cached intent analysis"""
        return self.intent_cache.get(text)

    async def set_cached_intent_analysis(self, text: str, analysis: Dict[str, Any]) -> bool:
        """Cache intent analysis"""
        self.intent_cache[text] = analysis
        return True

    async def get_cached_content_hash(self, content: str) -> Optional[str]:
        """Get cached content hash"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return self.content_cache.get(content_hash)

    async def set_cached_content_hash(self, content: str, post_id: str) -> bool:
        """Cache content hash"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        self.content_cache[content_hash] = post_id
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "url_cache_size": len(self.url_cache),
            "content_cache_size": len(self.content_cache),
            "intent_cache_size": len(self.intent_cache)
        }

    async def get(self, key: str, cache_type: str = 'default') -> Optional[str]:
        """Get cached value - simplified interface"""
        if cache_type == 'intent':
            return self.intent_cache.get(key)
        elif cache_type == 'url':
            return self.url_cache.get(key)
        else:
            return self.content_cache.get(key)

    async def set(self, key: str, value: str, ttl: int = 3600, cache_type: str = 'default') -> bool:
        """Set cached value - simplified interface"""
        if cache_type == 'intent':
            self.intent_cache[key] = value
        elif cache_type == 'url':
            self.url_cache[key] = value
        else:
            self.content_cache[key] = value
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "url_cache_size": len(self.url_cache),
            "content_cache_size": len(self.content_cache),
            "intent_cache_size": len(self.intent_cache)
        }

# Global instance
cache_manager = SimpleCacheManager()
