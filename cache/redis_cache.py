"""
Redis Integration for Aqxion Scraper
Distributed caching with fallback to local cache
"""

import asyncio
import json
from typing import Optional, Dict, Any, Union
import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError
import logging

from cache.simple_cache import SmartCacheManager

log = logging.getLogger("redis_cache")

class RedisCacheManager:
    """Redis-based distributed cache with local fallback"""

    def __init__(self, redis_url: str = "redis://localhost:6379", local_fallback: bool = True):
        self.redis_url = redis_url
        self.redis_client = None
        self.local_fallback = local_fallback
        self.local_cache = SmartCacheManager() if local_fallback else None
        self.connected = False

        # Redis connection settings
        self.max_retries = 3
        self.retry_delay = 1.0
        self.socket_timeout = 5.0
        self.socket_connect_timeout = 5.0

        log.info(f"🔴 Redis Cache Manager initialized - URL: {redis_url}")

    async def connect(self) -> bool:
        """Establish Redis connection"""
        try:
            self.redis_client = redis.Redis.from_url(
                self.redis_url,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                retry_on_timeout=True,
                max_connections=20,
                decode_responses=True
            )

            # Test connection
            await self.redis_client.ping()
            self.connected = True
            log.info("✅ Redis connection established successfully")
            return True

        except Exception as e:
            log.warning(f"❌ Redis connection failed: {e}")
            if self.local_fallback:
                log.info("🔄 Falling back to local cache")
            self.connected = False
            return False

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.connected = False
            log.info("🔌 Redis connection closed")

    def _make_key(self, key: str, namespace: str = "") -> str:
        """Create Redis key with namespace"""
        if namespace:
            return f"aqxion:{namespace}:{key}"
        return f"aqxion:{key}"

    def _serialize_value(self, value: Any) -> str:
        """Serialize value for Redis storage"""
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def _deserialize_value(self, value: str) -> Any:
        """Deserialize value from Redis storage"""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def _execute_with_retry(self, operation, *args, **kwargs):
        """Execute Redis operation with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if not self.connected:
                    await self.connect()

                if self.connected:
                    return await operation(*args, **kwargs)
                else:
                    raise ConnectionError("Redis not connected")

            except (ConnectionError, TimeoutError) as e:
                if attempt == self.max_retries - 1:
                    log.warning(f"❌ Redis operation failed after {self.max_retries} attempts: {e}")
                    raise e

                log.warning(f"⚠️ Redis operation failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff

    async def get(self, key: str, namespace: str = "") -> Optional[Any]:
        """Get value from Redis with local fallback"""
        redis_key = self._make_key(key, namespace)

        try:
            # Try Redis first
            if self.connected or await self.connect():
                value = await self._execute_with_retry(self.redis_client.get, redis_key)
                if value is not None:
                    log.debug(f"✅ Redis hit: {redis_key}")
                    return self._deserialize_value(value)

            # Fallback to local cache
            if self.local_fallback:
                local_value = await self.local_cache.get(key, namespace)
                if local_value is not None:
                    log.debug(f"🔄 Local cache hit: {key}")
                    # Also store in Redis for future requests
                    if self.connected:
                        try:
                            await self._execute_with_retry(
                                self.redis_client.set,
                                redis_key,
                                self._serialize_value(local_value),
                                ex=3600  # 1 hour TTL
                            )
                        except Exception:
                            pass  # Don't fail if Redis write fails
                    return local_value

        except Exception as e:
            log.warning(f"❌ Cache get error for key {key}: {e}")
            # Try local fallback if Redis fails
            if self.local_fallback:
                return await self.local_cache.get(key, namespace)

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None,
                  namespace: str = "") -> bool:
        """Set value in Redis with local fallback"""
        redis_key = self._make_key(key, namespace)
        serialized_value = self._serialize_value(value)

        try:
            # Try Redis first
            if self.connected or await self.connect():
                await self._execute_with_retry(
                    self.redis_client.set,
                    redis_key,
                    serialized_value,
                    ex=ttl or 3600
                )
                log.debug(f"✅ Redis set: {redis_key}")

            # Always store in local cache as backup
            if self.local_fallback:
                await self.local_cache.set(key, value, ttl, namespace)

            return True

        except Exception as e:
            log.warning(f"❌ Cache set error for key {key}: {e}")
            # Fallback to local cache only
            if self.local_fallback:
                return await self.local_cache.set(key, value, ttl, namespace)

        return False

    async def delete(self, key: str, namespace: str = "") -> bool:
        """Delete value from Redis and local cache"""
        redis_key = self._make_key(key, namespace)

        try:
            # Try Redis first
            if self.connected or await self.connect():
                await self._execute_with_retry(self.redis_client.delete, redis_key)
                log.debug(f"✅ Redis delete: {redis_key}")

            # Also delete from local cache
            if self.local_fallback:
                await self.local_cache.delete(key, namespace)

            return True

        except Exception as e:
            log.warning(f"❌ Cache delete error for key {key}: {e}")
            # Try local cache
            if self.local_fallback:
                return await self.local_cache.delete(key, namespace)

        return False

    async def exists(self, key: str, namespace: str = "") -> bool:
        """Check if key exists in Redis or local cache"""
        redis_key = self._make_key(key, namespace)

        try:
            # Try Redis first
            if self.connected or await self.connect():
                exists = await self._execute_with_retry(self.redis_client.exists, redis_key)
                if exists:
                    return True

            # Check local cache
            if self.local_fallback:
                return await self.local_cache.exists(key, namespace)

        except Exception as e:
            log.warning(f"❌ Cache exists error for key {key}: {e}")
            # Try local cache
            if self.local_fallback:
                return await self.local_cache.exists(key, namespace)

        return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "redis_connected": self.connected,
            "redis_url": self.redis_url,
            "local_fallback_enabled": self.local_fallback
        }

        try:
            if self.connected:
                info = await self._execute_with_retry(self.redis_client.info)
                stats.update({
                    "redis_memory_used": info.get("used_memory_human", "unknown"),
                    "redis_connected_clients": info.get("connected_clients", 0),
                    "redis_uptime_days": info.get("uptime_in_days", 0)
                })
        except Exception as e:
            log.warning(f"❌ Redis stats error: {e}")

        if self.local_fallback:
            local_stats = self.local_cache.get_metrics()
            stats["local_cache"] = local_stats

        return stats

    async def clear_namespace(self, namespace: str) -> bool:
        """Clear all keys in a namespace"""
        try:
            if self.connected or await self.connect():
                # Get all keys in namespace
                pattern = f"aqxion:{namespace}:*"
                keys = await self._execute_with_retry(self.redis_client.keys, pattern)

                if keys:
                    await self._execute_with_retry(self.redis_client.delete, *keys)
                    log.info(f"✅ Cleared {len(keys)} keys in namespace: {namespace}")

            # Clear local cache namespace (if implemented)
            if self.local_fallback and hasattr(self.local_cache, 'clear_namespace'):
                await self.local_cache.clear_namespace(namespace)

            return True

        except Exception as e:
            log.warning(f"❌ Clear namespace error for {namespace}: {e}")
            return False

# Global Redis cache manager
redis_cache = RedisCacheManager(redis_url="redis://localhost:6380")

async def init_redis_cache():
    """Initialize Redis cache connection"""
    await redis_cache.connect()

async def close_redis_cache():
    """Close Redis cache connection"""
    await redis_cache.disconnect()