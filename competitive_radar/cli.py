#!/usr/bin/env python3
"""
Competitive Radar CLI - Sistema Nervioso del Mercado

Interfaz de línea de comandos para el Competitive Radar.
Permite ejecutar sensores, procesar datos y generar señales.
Soporta múltiples formatos de output: JSON, CSV, Ejecutivo.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Optional

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from competitive_radar.sensors.google_search import GoogleSearchSensor
from competitive_radar.processors.data_extractor import DataExtractor
from competitive_radar.signals.business_signals import BusinessSignalsGenerator
from competitive_radar.dashboard.signal_dashboard import SignalDashboard
from competitive_radar.output.json_output import JSONOutputGenerator
from competitive_radar.output.csv_output import CSVOutputGenerator
from competitive_radar.output.executive_output import ExecutiveOutputGenerator

logger = logging.getLogger(__name__)

class CompetitiveRadarCLI:
    """CLI principal del Competitive Radar"""

    def __init__(self):
        self.google_sensor = GoogleSearchSensor()
        self.data_extractor = DataExtractor()
        self.signals_generator = BusinessSignalsGenerator()
        self.dashboard = SignalDashboard()

        # Generadores de output
        self.json_generator = JSONOutputGenerator()
        self.csv_generator = CSVOutputGenerator()
        self.executive_generator = ExecutiveOutputGenerator()

    async def run_sensor(self, sensor_type: str, keyword: str, limit: int = 10) -> dict:
        """Ejecutar un sensor específico"""
        logger.info(f"🚀 Ejecutando sensor: {sensor_type}")

        if sensor_type == "google":
            results = await self.google_sensor.search(keyword, limit=limit)
            logger.info(f"✅ Sensor completado: {len(results)} resultados")
            return {"sensor": sensor_type, "results": results}

        else:
            raise ValueError(f"Sensor no soportado: {sensor_type}")

    async def process_data(self, raw_data: dict) -> dict:
        """Procesar datos crudos"""
        logger.info("🧠 Procesando datos...")

        processed = await self.data_extractor.process(raw_data)
        logger.info("✅ Procesamiento completado")
        return processed

    async def generate_signals(self, processed_data: dict) -> dict:
        """Generar señales de negocio"""
        logger.info("🎯 Generando señales...")

        signals = await self.signals_generator.generate(processed_data)
        logger.info(f"✅ Generadas {len(signals)} señales")
        return signals

    async def show_dashboard(self, signals: dict) -> None:
        """Mostrar dashboard de señales"""
        logger.info("📊 Mostrando dashboard...")

        await self.dashboard.display(signals)

    async def run_full_scan(self, keyword: str, limit: int = 10, output_format: str = "executive", output_file: Optional[str] = None) -> dict:
        """Ejecutar escaneo completo: sensor → procesamiento → señales → output"""
        logger.info(f"🔍 Iniciando escaneo completo para: {keyword}")

        # 1. Ejecutar sensor
        raw_data = await self.run_sensor("google", keyword, limit)

        # 2. Procesar datos
        processed_data = await self.process_data(raw_data)

        # 3. Generar señales
        signals = await self.generate_signals(processed_data)

        # 4. Generar output según formato solicitado
        result_data = {
            "keyword": keyword,
            "raw_data": raw_data,
            "processed_data": processed_data,
            "signals": signals["signals"],  # Lista de objetos BusinessSignal
            "duration": 2.5,  # Simulado
            "pages_scanned": len(raw_data.get("results", [])),
            "sources": ["SERP", "Competidores"]
        }

        output_result = await self.generate_output(result_data, output_format, output_file)

        return result_data

    async def generate_output(self, data: dict, output_format: str, output_file: Optional[str] = None) -> dict:
        """Generar output en el formato solicitado"""
        logger.info(f"📊 Generando output en formato: {output_format}")

        # Seleccionar generador según formato
        if output_format == "json":
            generator = JSONOutputGenerator()
        elif output_format == "csv":
            generator = CSVOutputGenerator()
        elif output_format == "executive":
            generator = ExecutiveOutputGenerator()
        else:
            raise ValueError(f"Formato de output no soportado: {output_format}")

        # Generar output
        result = generator.generate(data, data["keyword"])

        # Si se especifica archivo, guardar
        if output_file:
            await self.save_output_to_file(result, output_format, output_file)
            logger.info(f"💾 Output guardado en: {output_file}")

        # Para executive, mostrar en consola
        if output_format == "executive":
            print(result[0])  # El texto ejecutivo

        return {"format": output_format, "result": result, "file": output_file}

    async def save_output_to_file(self, result: Any, output_format: str, output_file: str) -> None:
        """Guardar output en archivo"""
        import aiofiles

        if output_format == "json":
            content = json.dumps(result, indent=2, ensure_ascii=False)
        elif output_format == "csv":
            content = result  # Ya es string CSV
        elif output_format == "executive":
            content = result[0]  # El texto ejecutivo
        else:
            content = str(result)

        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            await f.write(content)


def create_parser() -> argparse.ArgumentParser:
    """Crear parser de argumentos"""
    parser = argparse.ArgumentParser(
        description="Competitive Radar - Sistema Nervioso del Mercado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Escaneo completo con output ejecutivo
  python -m competitive_radar.cli --keyword "limpieza piscina lima"

  # Output JSON para automatización
  python -m competitive_radar.cli --keyword "servicios piscina" --output-format json --output-file results.json

  # Output CSV para análisis
  python -m competitive_radar.cli --keyword "piscina miraflores" --output-format csv --output-file signals.csv

  # Solo sensor
  python -m competitive_radar.cli --sensor google --keyword "piscina miraflores"

  # Con límite específico
  python -m competitive_radar.cli --keyword "servicios piscina" --limit 20
        """
    )

    parser.add_argument(
        "--keyword",
        type=str,
        help="Palabra clave para búsqueda en el mercado"
    )

    parser.add_argument(
        "--sensor",
        type=str,
        choices=["google"],
        help="Tipo de sensor a ejecutar (opcional)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Límite de resultados (default: 10)"
    )

    parser.add_argument(
        "--output-format",
        type=str,
        choices=["json", "csv", "executive"],
        default="executive",
        help="Formato de output: json (automatización), csv (análisis), executive (humano) (default: executive)"
    )

    parser.add_argument(
        "--output-file",
        type=str,
        help="Archivo donde guardar el output (opcional)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Modo verbose con más información"
    )

    return parser


async def main():
    """Función principal"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.keyword:
        parser.print_help()
        return

    # Configurar logging
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.INFO)

    # Ejecutar radar
    cli = CompetitiveRadarCLI()

    try:
        if args.sensor:
            # Ejecutar solo sensor específico
            result = await cli.run_sensor(args.sensor, args.keyword, args.limit)
            print(f"📊 Resultados del sensor {args.sensor}: {len(result['results'])} encontrados")
        else:
            # Ejecutar escaneo completo
            result = await cli.run_full_scan(args.keyword, args.limit, args.output_format, args.output_file)
            print("🎉 Escaneo completo finalizado!")

    except Exception as e:
        logger.error(f"❌ Error ejecutando Competitive Radar: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
