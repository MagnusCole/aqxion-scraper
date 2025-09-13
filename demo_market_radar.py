#!/usr/bin/env python3
"""
Demo Rápido del Market Radar

Ejemplo de uso del sistema nervioso del mercado
"""

import asyncio
import sys
from pathlib import Path

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from market_radar.cli import MarketRadarCLI

async def demo_market_radar():
    """Demostración del Market Radar"""
    print("🚀 DEMO: Market Radar - Sistema Nervioso del Mercado")
    print("=" * 60)

    # Inicializar CLI
    cli = MarketRadarCLI()

    # Demo 1: Búsqueda básica
    print("\n📡 DEMO 1: BÚSQUEDA BÁSICA")
    print("-" * 30)

    keyword = "limpieza piscina lima"
    print(f"🎯 Buscando: '{keyword}'")

    try:
        # Ejecutar escaneo completo
        result = await cli.run_full_scan(keyword, limit=5)
        print("✅ Escaneo completado exitosamente!")

        # Mostrar resumen
        market_analysis = result["processed_data"]["market_analysis"]
        signals = result["signals"]

        print("\n📊 RESULTADOS:")
        print(f"   • Competidores encontrados: {market_analysis['total_companies']}")
        print(f"   • Servicios identificados: {len(market_analysis['services_distribution'])}")
        print(f"   • Señales generadas: {signals['total_signals']}")

        # Mostrar señales de alta prioridad
        high_priority = signals.get("high_priority_signals", [])
        if high_priority:
            print(f"\n🚨 SEÑALES CRÍTICAS:")
            for signal in high_priority:
                print(f"   • {signal.title} ({signal.confidence:.1%})")

    except Exception as e:
        print(f"❌ Error en demo: {e}")

    print("\n" + "=" * 60)
    print("🎉 Demo completado!")
    print("\n💡 Para uso completo:")
    print("   python -m market_radar.cli --keyword 'tu búsqueda'")
    print("\n📖 Ver documentación completa en MARKET_RADAR_README.md")

if __name__ == "__main__":
    asyncio.run(demo_market_radar())
