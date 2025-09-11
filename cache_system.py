"""
Sistema de caché inteligente para Aqxion Scraper
Implementa múltiples niveles de caché: memoria local, Redis distribuido, y persistente
"""

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

from cachetools import TTLCache, LRUCache
from config_v2 import get_settings

settings = get_settings()


@dataclass
class CacheEntry:
    """Estructura para entradas de caché"""
    key: str
    value: Any
    timestamp: float
    ttl: int
    metadata: Dict[str, Any] = None

    def is_expired(self) -> bool:
        """Verificar si la entrada ha expirado"""
        return time.time() - self.timestamp > self.ttl

    def to_dict(self) -> Dict:
        """Convertir a diccionario para serialización"""
        return {
            'key': self.key,
            'value': self.value,
            'timestamp': self.timestamp,
            'ttl': self.ttl,
            'metadata': self.metadata or {}
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheEntry':
        """Crear instancia desde diccionario"""
        return cls(
            key=data['key'],
            value=data['value'],
            timestamp=data['timestamp'],
            ttl=data['ttl'],
            metadata=data.get('metadata', {})
        )


class BaseCache:
    """Interfaz base para implementaciones de caché"""

    async def get(self, key: str) -> Optional[Any]:
        """Obtener valor de caché"""
        raise NotImplementedError

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Establecer valor en caché"""
        raise NotImplementedError

    async def delete(self, key: str) -> bool:
        """Eliminar valor de caché"""
        raise NotImplementedError

    async def clear(self) -> bool:
        """Limpiar toda la caché"""
        raise NotImplementedError

    async def has_key(self, key: str) -> bool:
        """Verificar si existe la clave"""
        raise NotImplementedError


class LocalCache(BaseCache):
    """Caché en memoria local usando cachetools"""

    def __init__(self, maxsize: int = 10000, ttl: int = 3600):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Obtener valor de caché local"""
        async with self._lock:
            return self.cache.get(key)

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Establecer valor en caché local"""
        async with self._lock:
            self.cache[key] = value
            return True

    async def delete(self, key: str) -> bool:
        """Eliminar valor de caché local"""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    async def clear(self) -> bool:
        """Limpiar caché local"""
        async with self._lock:
            self.cache.clear()
            return True

    async def has_key(self, key: str) -> bool:
        """Verificar si existe la clave"""
        async with self._lock:
            return key in self.cache


class RedisCache(BaseCache):
    """Caché distribuido usando Redis"""

    def __init__(self, url: str = None, ttl: int = 3600):
        if not REDIS_AVAILABLE:
            raise ImportError("Redis no está disponible. Instala redis-py: pip install redis")

        self.url = url or settings.cache.redis_url or "redis://localhost:6379"
        self.default_ttl = ttl
        self._pool = None

    async def _get_pool(self):
        """Obtener pool de conexiones Redis"""
        if self._pool is None:
            self._pool = redis.ConnectionPool.from_url(self.url)
        return redis.Redis(connection_pool=self._pool)

    async def get(self, key: str) -> Optional[Any]:
        """Obtener valor de Redis"""
        try:
            r = await self._get_pool()
            data = await r.get(key)
            if data:
                # Deserializar JSON
                return json.loads(data.decode('utf-8'))
            return None
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Establecer valor en Redis"""
        try:
            r = await self._get_pool()
            ttl_value = ttl or self.default_ttl
            # Serializar a JSON
            data = json.dumps(value, default=str)
            return await r.setex(key, ttl_value, data)
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """Eliminar valor de Redis"""
        try:
            r = await self._get_pool()
            return await r.delete(key) > 0
        except Exception:
            return False

    async def clear(self) -> bool:
        """Limpiar toda la caché Redis"""
        try:
            r = await self._get_pool()
            return await r.flushdb()
        except Exception:
            return False

    async def has_key(self, key: str) -> bool:
        """Verificar si existe la clave en Redis"""
        try:
            r = await self._get_pool()
            return await r.exists(key) > 0
        except Exception:
            return False


class MultiLevelCache:
    """Caché multinivel: local + Redis + persistente"""

    def __init__(self):
        self.local_cache = LocalCache(
            maxsize=settings.cache.local_cache_size,
            ttl=settings.cache.local_cache_ttl
        )

        self.redis_cache = None
        if REDIS_AVAILABLE and settings.cache.redis_url:
            try:
                self.redis_cache = RedisCache(
                    url=settings.cache.redis_url,
                    ttl=settings.cache.redis_ttl
                )
            except Exception:
                self.redis_cache = None

        # Estadísticas de rendimiento
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }

    async def get(self, key: str) -> Optional[Any]:
        """Obtener valor con estrategia multinivel"""
        # 1. Intentar caché local primero
        value = await self.local_cache.get(key)
        if value is not None:
            self.stats['hits'] += 1
            return value

        # 2. Intentar Redis si está disponible
        if self.redis_cache:
            value = await self.redis_cache.get(key)
            if value is not None:
                # Popular caché local
                await self.local_cache.set(key, value)
                self.stats['hits'] += 1
                return value

        self.stats['misses'] += 1
        return None

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Establecer valor en múltiples niveles"""
        success = True

        # 1. Establecer en caché local
        local_success = await self.local_cache.set(key, value, ttl)
        success &= local_success

        # 2. Establecer en Redis si está disponible
        if self.redis_cache:
            redis_success = await self.redis_cache.set(key, value, ttl)
            success &= redis_success

        if success:
            self.stats['sets'] += 1

        return success

    async def delete(self, key: str) -> bool:
        """Eliminar de todos los niveles"""
        local_success = await self.local_cache.delete(key)
        redis_success = True

        if self.redis_cache:
            redis_success = await self.redis_cache.delete(key)

        if local_success or redis_success:
            self.stats['deletes'] += 1
            return True

        return False

    async def clear(self) -> bool:
        """Limpiar todos los niveles"""
        local_success = await self.local_cache.clear()
        redis_success = True

        if self.redis_cache:
            redis_success = await self.redis_cache.clear()

        return local_success and redis_success

    async def has_key(self, key: str) -> bool:
        """Verificar si existe en algún nivel"""
        if await self.local_cache.has_key(key):
            return True

        if self.redis_cache:
            return await self.redis_cache.has_key(key)

        return False

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de rendimiento"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            **self.stats,
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests,
            'redis_enabled': self.redis_cache is not None
        }


class CacheManager:
    """Gestor centralizado de caché con estrategias específicas"""

    def __init__(self):
        self.cache = MultiLevelCache()

        # Caches especializados
        self.url_cache = MultiLevelCache()
        self.content_cache = MultiLevelCache()
        self.intent_cache = MultiLevelCache()

    # === MÉTODOS DE CACHE GENERAL ===

    async def get(self, key: str, cache_type: str = 'general') -> Optional[Any]:
        """Obtener valor de caché específica"""
        cache = self._get_cache(cache_type)
        return await cache.get(key)

    async def set(self, key: str, value: Any, ttl: int = None, cache_type: str = 'general') -> bool:
        """Establecer valor en caché específica"""
        cache = self._get_cache(cache_type)
        return await cache.set(key, value, ttl)

    async def delete(self, key: str, cache_type: str = 'general') -> bool:
        """Eliminar valor de caché específica"""
        cache = self._get_cache(cache_type)
        return await cache.delete(key)

    async def has_key(self, key: str, cache_type: str = 'general') -> bool:
        """Verificar si existe clave en caché específica"""
        cache = self._get_cache(cache_type)
        return await cache.has_key(key)

    def _get_cache(self, cache_type: str) -> MultiLevelCache:
        """Obtener instancia de caché por tipo"""
        if cache_type == 'url' and settings.cache.enable_url_cache:
            return self.url_cache
        elif cache_type == 'content' and settings.cache.enable_content_cache:
            return self.content_cache
        elif cache_type == 'intent' and settings.cache.enable_intent_cache:
            return self.intent_cache
        else:
            return self.cache

    # === MÉTODOS ESPECIALIZADOS ===

    async def get_cached_url_content(self, url: str) -> Optional[str]:
        """Obtener contenido de URL cacheado"""
        cache_key = f"url:{hashlib.md5(url.encode()).hexdigest()}"
        return await self.get(cache_key, 'url')

    async def set_cached_url_content(self, url: str, content: str, ttl: int = None) -> bool:
        """Cachear contenido de URL"""
        cache_key = f"url:{hashlib.md5(url.encode()).hexdigest()}"
        ttl_value = ttl or settings.cache.redis_ttl
        return await self.set(cache_key, content, ttl_value, 'url')

    async def get_cached_intent_analysis(self, text: str) -> Optional[str]:
        """Obtener análisis de intención cacheado"""
        cache_key = f"intent:{hashlib.md5(text[:500].encode()).hexdigest()}"
        return await self.get(cache_key, 'intent')

    async def set_cached_intent_analysis(self, text: str, intent: str, ttl: int = None) -> bool:
        """Cachear análisis de intención"""
        cache_key = f"intent:{hashlib.md5(text[:500].encode()).hexdigest()}"
        ttl_value = ttl or settings.cache.redis_ttl
        return await self.set(cache_key, intent, ttl_value, 'intent')

    async def get_cached_content_hash(self, content: str) -> Optional[str]:
        """Obtener hash de contenido cacheado (para deduplicación)"""
        content_hash = hashlib.md5(content[:1000].encode()).hexdigest()
        cache_key = f"content:{content_hash}"
        return await self.get(cache_key, 'content')

    async def set_cached_content_hash(self, content: str, post_id: str, ttl: int = None) -> bool:
        """Cachear hash de contenido para deduplicación"""
        content_hash = hashlib.md5(content[:1000].encode()).hexdigest()
        cache_key = f"content:{content_hash}"
        ttl_value = ttl or (settings.cache.redis_ttl * 7)  # 7 días para deduplicación
        return await self.set(cache_key, post_id, ttl_value, 'content')

    # === MÉTODOS DE MANTENIMIENTO ===

    async def cleanup_expired(self) -> Dict[str, int]:
        """Limpiar entradas expiradas (simplificado - en producción usar Redis TTL)"""
        # En Redis, las entradas expiradas se limpian automáticamente
        # Aquí solo limpiamos estadísticas locales
        result = {
            'general_cleaned': 0,
            'url_cleaned': 0,
            'content_cleaned': 0,
            'intent_cleaned': 0
        }

        # Reset stats periodically
        if self.cache.stats['total_requests'] > 10000:
            self.cache.stats = {k: 0 for k in self.cache.stats}

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de todas las cachés"""
        return {
            'general': self.cache.get_stats(),
            'url': self.url_cache.get_stats(),
            'content': self.content_cache.get_stats(),
            'intent': self.intent_cache.get_stats(),
            'redis_available': REDIS_AVAILABLE and settings.cache.redis_url is not None
        }

    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud del sistema de caché"""
        health = {
            'local_cache': True,
            'redis_cache': False,
            'overall_health': True
        }

        # Verificar Redis si está configurado
        if self.redis_cache:
            try:
                # Intentar una operación simple
                test_key = 'health_check'
                await self.redis_cache.set(test_key, 'ok', 10)
                result = await self.redis_cache.get(test_key)
                health['redis_cache'] = result == 'ok'
                await self.redis_cache.delete(test_key)
            except Exception:
                health['redis_cache'] = False

        health['overall_health'] = health['local_cache'] and (not self.redis_cache or health['redis_cache'])
        return health


# Instancia global del gestor de caché
cache_manager = CacheManager()


async def get_cache_manager() -> CacheManager:
    """Obtener instancia global del gestor de caché"""
    return cache_manager


# Funciones de conveniencia para uso síncrono
def get_cached_url_content_sync(url: str) -> Optional[str]:
    """Versión síncrona para compatibilidad"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Si ya hay un loop corriendo, crear una tarea
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, cache_manager.get_cached_url_content(url))
                return future.result(timeout=5)
        else:
            return loop.run_until_complete(cache_manager.get_cached_url_content(url))
    except Exception:
        return None


def set_cached_url_content_sync(url: str, content: str, ttl: int = None) -> bool:
    """Versión síncrona para compatibilidad"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, cache_manager.set_cached_url_content(url, content, ttl))
                return future.result(timeout=5)
        else:
            return loop.run_until_complete(cache_manager.set_cached_url_content(url, content, ttl))
    except Exception:
        return False
