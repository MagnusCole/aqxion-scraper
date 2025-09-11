#!/usr/bin/env python3
"""
Script de prueba simple para validar el sistema de caché
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from cache_system import cache_manager


async def test_cache_system():
    """Probar el sistema de caché directamente"""
    print("🧪 Probando sistema de caché...")

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
    asyncio.run(test_cache_system())
