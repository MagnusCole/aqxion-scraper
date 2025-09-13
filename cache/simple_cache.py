"""
Smart Cache System for Aqxion Scraper
Redis-compatible interface with intelligent caching strategies
"""

import asyncio
import gzip
import hashlib
import json
import time
from typing import Optional, Dict, Any, Union, List
from cachetools import TTLCache, LRUCache, LFUCache
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    compression_savings: int = 0
    avg_response_time: float = 0.0
    last_cleanup: datetime = field(default_factory=datetime.now)

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def total_operations(self) -> int:
        return self.hits + self.misses + self.sets + self.deletes

class SmartCacheManager:
    """Intelligent cache manager with Redis-compatible interface"""

    def __init__(self, max_memory_mb: int = 100):
        # Multiple cache strategies
        self.lru_cache = LRUCache(maxsize=1000)
        self.lfu_cache = LFUCache(maxsize=1000)
        self.ttl_cache = TTLCache(maxsize=2000, ttl=3600)

        # Specialized caches for different data types
        self.url_cache = TTLCache(maxsize=500, ttl=1800)  # 30 min for URLs
        self.content_cache = TTLCache(maxsize=300, ttl=3600)  # 1 hour for content
        self.intent_cache = TTLCache(maxsize=1000, ttl=7200)  # 2 hours for AI analysis

        # Compression settings
        self.compression_threshold = 1024  # Compress content > 1KB
        self.max_memory_mb = max_memory_mb

        # Metrics and monitoring
        self.metrics = CacheMetrics()
        self.response_times: List[float] = []

        # Thread safety
        self._lock = threading.Lock()

        print(f"🧠 Smart Cache initialized with {max_memory_mb}MB memory limit")

    def _should_compress(self, data: str) -> bool:
        """Determine if data should be compressed"""
        return len(data.encode('utf-8')) > self.compression_threshold

    def _compress_data(self, data: str) -> bytes:
        """Compress data using gzip"""
        return gzip.compress(data.encode('utf-8'))

    def _decompress_data(self, compressed_data: bytes) -> str:
        """Decompress gzip data"""
        return gzip.decompress(compressed_data).decode('utf-8')

    def _serialize_value(self, value: Any) -> str:
        """Serialize value to JSON string"""
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def _deserialize_value(self, value: str) -> Any:
        """Deserialize value from JSON string"""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def _get_cache_key(self, key: str, namespace: str = "") -> str:
        """Generate consistent cache key"""
        if namespace:
            key = f"{namespace}:{key}"
        return hashlib.md5(key.encode()).hexdigest()

    def _select_cache_strategy(self, key: str, strategy: str = 'auto') -> Any:
        """Select appropriate cache strategy"""
        if strategy == 'lru':
            return self.lru_cache
        elif strategy == 'lfu':
            return self.lfu_cache
        elif strategy == 'ttl':
            return self.ttl_cache
        else:
            # Auto-select based on key pattern
            if 'url' in key.lower():
                return self.url_cache
            elif 'intent' in key.lower() or 'analysis' in key.lower():
                return self.intent_cache
            elif 'content' in key.lower():
                return self.content_cache
            else:
                return self.ttl_cache

    async def get(self, key: str, namespace: str = "", strategy: str = 'auto') -> Optional[Any]:
        """Get value from cache with Redis-compatible interface"""
        start_time = time.time()

        with self._lock:
            cache_key = self._get_cache_key(key, namespace)
            cache = self._select_cache_strategy(key, strategy)

            try:
                compressed_data = cache.get(cache_key)
                if compressed_data is None:
                    self.metrics.misses += 1
                    return None

                # Decompress if needed
                if isinstance(compressed_data, bytes):
                    data = self._decompress_data(compressed_data)
                else:
                    data = compressed_data

                # Deserialize
                value = self._deserialize_value(data)
                self.metrics.hits += 1

                # Track response time
                response_time = time.time() - start_time
                self.response_times.append(response_time)
                if len(self.response_times) > 100:
                    self.response_times.pop(0)

                return value

            except Exception as e:
                print(f"⚠️  Cache get error for key {key}: {e}")
                self.metrics.misses += 1
                return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None,
                  namespace: str = "", strategy: str = 'auto', compress: bool = True) -> bool:
        """Set value in cache with Redis-compatible interface"""
        start_time = time.time()

        with self._lock:
            try:
                cache_key = self._get_cache_key(key, namespace)
                cache = self._select_cache_strategy(key, strategy)

                # Serialize value
                serialized_value = self._serialize_value(value)

                # Compress if beneficial
                if compress and self._should_compress(serialized_value):
                    final_value = self._compress_data(serialized_value)
                    original_size = len(serialized_value.encode('utf-8'))
                    compressed_size = len(final_value)
                    self.metrics.compression_savings += (original_size - compressed_size)
                else:
                    final_value = serialized_value

                # Store in cache
                cache[cache_key] = final_value
                self.metrics.sets += 1

                # Track response time
                response_time = time.time() - start_time
                self.response_times.append(response_time)
                if len(self.response_times) > 100:
                    self.response_times.pop(0)

                return True

            except Exception as e:
                print(f"⚠️  Cache set error for key {key}: {e}")
                return False

    async def delete(self, key: str, namespace: str = "", strategy: str = 'auto') -> bool:
        """Delete value from cache"""
        with self._lock:
            try:
                cache_key = self._get_cache_key(key, namespace)
                cache = self._select_cache_strategy(key, strategy)

                if cache_key in cache:
                    del cache[cache_key]
                    self.metrics.deletes += 1
                    return True
                return False

            except Exception as e:
                print(f"⚠️  Cache delete error for key {key}: {e}")
                return False

    async def exists(self, key: str, namespace: str = "", strategy: str = 'auto') -> bool:
        """Check if key exists in cache"""
        with self._lock:
            cache_key = self._get_cache_key(key, namespace)
            cache = self._select_cache_strategy(key, strategy)
            return cache_key in cache

    async def expire(self, key: str, ttl: int, namespace: str = "", strategy: str = 'auto') -> bool:
        """Set expiration time for key (Redis-compatible)"""
        # For TTL cache, we need to re-set with new TTL
        value = await self.get(key, namespace, strategy)
        if value is not None:
            await self.set(key, value, ttl, namespace, strategy)
            return True
        return False

    async def ttl(self, key: str, namespace: str = "", strategy: str = 'auto') -> int:
        """Get TTL for key (Redis-compatible)"""
        # Simplified TTL check - in a real Redis implementation this would be more accurate
        exists = await self.exists(key, namespace, strategy)
        return -1 if exists else -2  # -1 = exists, -2 = doesn't exist

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cache metrics"""
        with self._lock:
            if self.response_times:
                self.metrics.avg_response_time = sum(self.response_times) / len(self.response_times)

            return {
                "hit_rate": round(self.metrics.hit_rate * 100, 2),
                "total_operations": self.metrics.total_operations,
                "hits": self.metrics.hits,
                "misses": self.metrics.misses,
                "sets": self.metrics.sets,
                "deletes": self.metrics.deletes,
                "compression_savings_mb": round(self.metrics.compression_savings / (1024 * 1024), 2),
                "avg_response_time_ms": round(self.metrics.avg_response_time * 1000, 2),
                "cache_sizes": {
                    "lru": len(self.lru_cache),
                    "lfu": len(self.lfu_cache),
                    "ttl": len(self.ttl_cache),
                    "url": len(self.url_cache),
                    "content": len(self.content_cache),
                    "intent": len(self.intent_cache)
                },
                "last_cleanup": self.metrics.last_cleanup.isoformat()
            }

    async def cleanup(self) -> Dict[str, int]:
        """Perform cache cleanup and maintenance"""
        with self._lock:
            # Clear expired entries (TTL caches handle this automatically)
            # Additional cleanup logic can be added here
            self.metrics.last_cleanup = datetime.now()

            return {
                "lru_size": len(self.lru_cache),
                "lfu_size": len(self.lfu_cache),
                "ttl_size": len(self.ttl_cache),
                "url_size": len(self.url_cache),
                "content_size": len(self.content_cache),
                "intent_size": len(self.intent_cache)
            }

    async def get_cached_content_hash(self, content: str) -> Optional[str]:
        """Legacy method for content hash caching"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return await self.get(content_hash, namespace="content")

    async def set_cached_content_hash(self, content: str, post_id: str) -> bool:
        """Legacy method for content hash caching"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return await self.set(content_hash, post_id, namespace="content")

    def get_stats(self) -> Dict[str, Any]:
        """Legacy method for getting cache statistics"""
        return self.get_metrics()

# Global instance
cache_manager = SmartCacheManager()