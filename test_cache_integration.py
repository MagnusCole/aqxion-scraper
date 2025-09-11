#!/usr/bin/env python3
"""
Script de prueba para validar la integración del sistema de caché en main_async.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from main_async import AsyncScraper
from cache_system import cache_manager


async def test_cache_integration():
    """Probar la integración del sistema de caché"""
    print("🧪 Probando integración del sistema de caché...")

    # Inicializar scraper
    async with AsyncScraper() as scraper:
        print("✅ Scraper inicializado correctamente")

        # Probar estadísticas de caché
        try:
            stats = await scraper.get_cache_stats()
            print(f"✅ Estadísticas de caché obtenidas: {stats}")
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas: {e}")

        # Probar limpieza de caché
        try:
            success = await scraper.clear_cache('url')
            print(f"✅ Limpieza de caché URL: {'exitosa' if success else 'fallida'}")
        except Exception as e:
            print(f"❌ Error limpiando caché: {e}")

        # Probar métodos de deduplicación
        test_content = "Este es un contenido de prueba para deduplicación"
        try:
            # Verificar que no existe
            is_duplicate, existing_id = await scraper.is_content_duplicate(test_content)
            print(f"✅ Verificación inicial de duplicado: {is_duplicate}")

            # Cachear contenido
            test_post_id = "test_post_123"
            success = await scraper.cache_content_hash(test_content, test_post_id)
            print(f"✅ Cacheo de contenido: {'exitosa' if success else 'fallida'}")

            # Verificar que ahora existe
            is_duplicate, existing_id = await scraper.is_content_duplicate(test_content)
            print(f"✅ Verificación de duplicado después de cacheo: {is_duplicate}, ID: {existing_id}")

        except Exception as e:
            print(f"❌ Error en pruebas de deduplicación: {e}")

    print("🎉 Pruebas completadas!")


if __name__ == "__main__":
    asyncio.run(test_cache_integration())
