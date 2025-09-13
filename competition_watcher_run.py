#!/usr/bin/env python3
"""
Competition Watcher Runner
Script independiente para ejecutar análisis de competencia
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from scraping.competition_watcher import competition_watcher

def show_analysis_summary(analysis, output_path):
    """Mostrar resumen del análisis"""
    print("📈 RESUMEN DE MERCADO:")
    print("-" * 30)

    if analysis.service_categories:
        print("🎯 Servicios más ofrecidos:")
        for service, count in analysis.service_categories.items():
            print(f"  • {service}: {count} competidores")

    if analysis.locations:
        print("\n📍 Distribución geográfica:")
        for location, count in analysis.locations.items():
            print(f"  • {location}: {count} competidores")

    if analysis.price_ranges:
        print("\n💰 Información de precios:")
        for price_type, count in analysis.price_ranges.items():
            print(f"  • {price_type}: {count} competidores")

    # Generar y mostrar reporte
    print("\n📋 Generando reporte completo...")
    report = competition_watcher.generate_report(output_path)

    if output_path:
        print(f"💾 Reporte guardado en: {output_path}")
    else:
        print("\n" + "="*60)
        print("📄 REPORTE COMPLETO:")
        print("="*60)
        print(report)

async def run_full_mode(args):
    """Modo completo: recolectar + analizar"""
    print("🚀 Iniciando análisis completo de competencia...")

    analysis = await competition_watcher.run_full_analysis(args.max_competitors)

    print("\n✅ Análisis completado!")
    print(f"🏢 Competidores encontrados: {analysis.total_competitors}")
    print()

    show_analysis_summary(analysis, args.output)

async def run_collect_mode(args):
    """Modo solo recolección"""
    print("📥 Iniciando recolección de datos...")

    competitors_found = await competition_watcher.collect_competitor_data(args.max_competitors)

    print("\n✅ Recolección completada!")
    print(f"💾 {competitors_found} competidores guardados en base de datos")
    print("\n💡 Para analizar estos datos, ejecuta:")
    print(f"python competition_watcher_run.py --mode analyze --keyword \"{args.keyword}\"")

async def run_analyze_mode(args):
    """Modo solo análisis"""
    print("🔬 Iniciando análisis de datos existentes...")

    # Cargar datos
    competitors = competition_watcher.load_competitor_data(args.load_limit)

    if not competitors:
        print("❌ No se encontraron datos de competidores para analizar")
        print("💡 Primero recolecta datos con: --mode collect")
        return

    print(f"📂 Analizando {len(competitors)} competidores...")

    # Analizar
    analysis = await competition_watcher.analyze_competitor_data()

    print("\n✅ Análisis completado!")
    show_analysis_summary(analysis, args.output)

def run_history_mode(args):
    """Modo historial"""
    print("📚 Consultando historial...")

    # Historial de análisis
    analyses = competition_watcher.get_analysis_history(args.history_limit)

    if analyses:
        print(f"\n📊 ÚLTIMOS {len(analyses)} ANÁLISIS:")
        print("-" * 50)
        for i, analysis in enumerate(analyses, 1):
            print(f"{i}. {analysis['keyword']} - {analysis['total_competitors']} competidores")
            print(f"   📅 {analysis['analyzed_at'][:19]}")
            if analysis['market_gaps']:
                print(f"   💡 Gaps: {len(analysis['market_gaps'])}")
            print()
    else:
        print("❌ No se encontraron análisis previos")

    # Historial de ejecuciones
    runs = competition_watcher.get_run_history(args.history_limit)

    if runs:
        print(f"\n⚙️ ÚLTIMAS {len(runs)} EJECUCIONES:")
        print("-" * 50)
        for i, run in enumerate(runs, 1):
            status_emoji = "✅" if run['status'] == 'completed' else "❌" if run['status'] == 'failed' else "⏳"
            print(f"{i}. {run['run_type']} - {status_emoji} {run['status']}")
            print(f"   📅 {run['started_at'][:19]}")
            print(f"   🎯 {run['competitors_found']} competidores")
            if run['error_message']:
                print(f"   ⚠️ {run['error_message']}")
            print()

async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Competition Watcher - Análisis de Competencia')
    parser.add_argument('--mode', choices=['full', 'collect', 'analyze', 'history'],
                       default='full',
                       help='Modo de operación: full (recolectar+analizar), collect (solo recolectar), analyze (solo analizar), history (ver historial)')
    parser.add_argument('--max-competitors', type=int, default=10,
                       help='Máximo número de competidores a analizar (default: 10)')
    parser.add_argument('--output', type=str,
                       help='Ruta donde guardar el reporte (opcional)')
    parser.add_argument('--keyword', type=str,
                       default="limpieza de piscina lima",
                       help='Keyword a buscar (default: "limpieza de piscina lima")')
    parser.add_argument('--load-limit', type=int, default=None,
                       help='Límite de competidores a cargar para análisis (solo para modo analyze)')
    parser.add_argument('--history-limit', type=int, default=5,
                       help='Límite de registros de historial a mostrar')

    args = parser.parse_args()

    print("🔍 COMPETITION WATCHER")
    print("=" * 50)
    print(f"📊 Modo: {args.mode}")
    print(f"🎯 Keyword: {args.keyword}")

    if args.mode == 'full':
        print(f"🎯 Máximo competidores: {args.max_competitors}")
    elif args.mode == 'collect':
        print(f"� Máximo competidores: {args.max_competitors}")
    elif args.mode == 'analyze':
        print(f"🎯 Límite de carga: {args.load_limit or 'todos'}")
    elif args.mode == 'history':
        print(f"🎯 Límite de historial: {args.history_limit}")

    print()

    try:
        # Configurar keyword si es diferente
        if args.keyword != competition_watcher.keyword:
            competition_watcher.keyword = args.keyword

        # Ejecutar según el modo
        if args.mode == 'full':
            await run_full_mode(args)
        elif args.mode == 'collect':
            await run_collect_mode(args)
        elif args.mode == 'analyze':
            await run_analyze_mode(args)
        elif args.mode == 'history':
            run_history_mode(args)

    except KeyboardInterrupt:
        print("\n⏹️  Operación interrumpida por el usuario")
        return 1
    except Exception as e:
        print(f"\n❌ Error durante la operación: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
