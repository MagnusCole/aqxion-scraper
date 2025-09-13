#!/usr/bin/env python3
"""
Ejemplo rápido de uso del Competition Watcher
Demuestra los nuevos modos: collect, analyze, full
"""

import asyncio
import sys
from pathlib import Path

# Agregar raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from scraping.competition_watcher import competition_watcher

async def demo():
    """Demostración de los diferentes modos del Competition Watcher"""
    print("🔍 DEMO: Competition Watcher v2.0")
    print("=" * 50)
    print("🚀 Nuevos modos disponibles:")
    print("  • collect: Solo recolectar datos")
    print("  • analyze: Solo analizar datos existentes")
    print("  • full: Recolectar + analizar (modo original)")
    print("  • history: Ver historial de ejecuciones")
    print()

    # Demo 1: Modo collect
    print("📥 DEMO 1: MODO COLLECT (Solo recolección)")
    print("-" * 40)
    try:
        print("🎯 Recolectando datos de 3 competidores...")
        competitors_found = await competition_watcher.collect_competitor_data(max_competitors=3)
        print(f"✅ Recolectados y guardados: {competitors_found} competidores")
    except Exception as e:
        print(f"⚠️ Error en recolección: {e}")

    print()

    # Demo 2: Modo analyze
    print("🔬 DEMO 2: MODO ANALYZE (Solo análisis)")
    print("-" * 40)
    try:
        print("📂 Cargando datos desde base de datos...")
        competitors = competition_watcher.load_competitor_data(limit=5)
        print(f"📊 Datos cargados: {len(competitors)} competidores")

        if competitors:
            print("🔍 Analizando datos...")
            analysis = await competition_watcher.analyze_competitor_data()
            print(f"✅ Análisis completado: {analysis.total_competitors} competidores")

            # Mostrar resumen rápido
            if analysis.service_categories:
                print("🎯 Servicios encontrados:")
                for service, count in list(analysis.service_categories.items())[:3]:
                    print(f"  • {service}: {count}")
        else:
            print("❌ No hay datos para analizar")

    except Exception as e:
        print(f"⚠️ Error en análisis: {e}")

    print()

    # Demo 3: Historial
    print("📚 DEMO 3: HISTORIAL DE EJECUCIONES")
    print("-" * 40)
    try:
        runs = competition_watcher.get_run_history(limit=3)
        if runs:
            print(f"📋 Últimas {len(runs)} ejecuciones:")
            for run in runs:
                status = "✅" if run['status'] == 'completed' else "❌" if run['status'] == 'failed' else "⏳"
                print(f"  {status} {run['run_type']} - {run['competitors_found']} comps")
        else:
            print("❌ No hay historial de ejecuciones")
    except Exception as e:
        print(f"⚠️ Error obteniendo historial: {e}")

    print()
    print("🎉 DEMO COMPLETADA")
    print()
    print("💡 Usos prácticos:")
    print("1. Recolecta datos periódicamente: --mode collect")
    print("2. Analiza datos existentes: --mode analyze")
    print("3. Análisis completo único: --mode full")
    print("4. Revisa historial: --mode history")
    print()
    print("📖 Para más opciones:")
    print("python competition_watcher_run.py --help")

if __name__ == "__main__":
    asyncio.run(demo())
