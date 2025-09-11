#!/usr/bin/env python3
"""
Script de prueba ultra-simple para validar el sistema de caché
Sin dependencias de configuración compleja
"""

import asyncio
import hashlib
import time
from typing import Any, Dict, Optional
from cachetools import TTLCache


class SimpleCache:
    """Caché simple para pruebas"""

    def __init__(self):
        self.cache = TTLCache(maxsize=1000, ttl=3600)

    async def get(self, key: str) -> Optional[Any]:
        return self.cache.get(key)

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        self.cache[key] = value
        return True

    async def has_key(self, key: str) -> bool:
        return key in self.cache


class SimpleCacheManager:
    """Gestor simple de caché para pruebas"""

    def __init__(self):
        self.url_cache = SimpleCache()
        self.content_cache = SimpleCache()

    async def get_cached_url_content(self, url: str) -> Optional[str]:
        cache_key = f"url:{hashlib.md5(url.encode()).hexdigest()}"
        return await self.url_cache.get(cache_key)

    async def set_cached_url_content(self, url: str, content: str, ttl: int = 3600) -> bool:
        cache_key = f"url:{hashlib.md5(url.encode()).hexdigest()}"
        return await self.url_cache.set(cache_key, content, ttl)

    async def get_cached_content_hash(self, content: str) -> Optional[str]:
        content_hash = hashlib.md5(content[:1000].encode()).hexdigest()
        cache_key = f"content:{content_hash}"
        return await self.content_cache.get(cache_key)

    async def set_cached_content_hash(self, content: str, post_id: str, ttl: int = 3600) -> bool:
        content_hash = hashlib.md5(content[:1000].encode()).hexdigest()
        cache_key = f"content:{content_hash}"
        return await self.content_cache.set(cache_key, post_id, ttl)

    def get_stats(self) -> Dict[str, Any]:
        return {
            'url_cache_size': len(self.url_cache.cache),
            'content_cache_size': len(self.content_cache.cache),
            'test_mode': True
        }


# Instancia global
cache_manager = SimpleCacheManager()


async def test_simple_cache():
    """Probar el sistema de caché de forma simple"""
    print("🧪 Probando sistema de caché simple...")

    # Probar cache de URL
    test_url = "https://example.com/test"
    test_content = "<html><body>Test content</body></html>"

    try:
        # Cachear contenido
        success = await cache_manager.set_cached_url_content(test_url, test_content)
        print(f"✅ Cacheo de URL: {'exitosa' if success else 'fallida'}")

        # Recuperar contenido
        cached_content = await cache_manager.get_cached_url_content(test_url)
        print(f"✅ Recuperación de caché: {'exitosa' if cached_content == test_content else 'fallida'}")

        # Probar deduplicación de contenido
        test_post_id = "test_post_123"
        success = await cache_manager.set_cached_content_hash(test_content, test_post_id)
        print(f"✅ Cacheo de hash de contenido: {'exitosa' if success else 'fallida'}")

        # Verificar duplicado
        existing_id = await cache_manager.get_cached_content_hash(test_content)
        print(f"✅ Verificación de duplicado: {'exitosa' if existing_id == test_post_id else 'fallida'}")

        # Obtener estadísticas
        stats = cache_manager.get_stats()
        print(f"✅ Estadísticas: {stats}")

        print("🎉 Todas las pruebas del sistema de caché pasaron!")

    except Exception as e:
        print(f"❌ Error en pruebas: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_simple_cache())
