#!/usr/bin/env python3
"""
Script de cierre diario para Aqxion Scraper
Ejecuta exportaciones, genera reportes y envía alertas
"""

import os
import sys
import logging
from datetime import datetime
from export_daily_enhanced import DailyExporter
from alerts import alert_daily_summary, alert_system_status
from kpi import kpi  # Para calcular KPIs

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger("daily_close")

def calculate_daily_kpis():
    """Calcular KPIs del día y devolver resumen"""
    # Aquí iría la lógica para calcular KPIs
    # Por ahora, devolver valores de ejemplo
    return {
        'dolores': 15,
        'busquedas': 8,
        'objeciones': 5,
        'ruido': 25,
        'total': 53,
        'intencion_pct': 53.0
    }

def get_top_keywords():
    """Obtener top keywords del día"""
    # Aquí iría la lógica para obtener top keywords
    # Por ahora, devolver valores de ejemplo
    return [
        ("agencia marketing digital", 12),
        ("consultoria marketing", 8),
        ("marketing digital peru", 6),
        ("empresa marketing lima", 5),
        ("marketing online peru", 4)
    ]

def run_daily_close():
    """Ejecutar cierre diario completo"""
    log.info("🚀 Iniciando cierre diario de Aqxion Scraper")

    try:
        # 1. Calcular KPIs
        log.info("📊 Calculando KPIs del día...")
        kpis = calculate_daily_kpis()
        log.info(f"KPIs calculados: {kpis}")

        # 2. Obtener top keywords
        log.info("🏆 Obteniendo top keywords...")
        top_keywords = get_top_keywords()
        log.info(f"Top keywords: {top_keywords}")

        # 3. Exportar datos
        log.info("📁 Exportando datos diarios...")
        exporter = DailyExporter()
        export_files = exporter.export_all_daily("exports")

        if export_files:
            log.info(f"✅ Archivos exportados: {export_files}")
        else:
            log.warning("⚠️ No se generaron archivos de exportación")

        # 4. Enviar alerta de resumen diario
        log.info("📢 Enviando resumen diario por Telegram...")
        alert_daily_summary(
            actionable_dolores=kpis['dolores'],
            provider_searches=kpis['busquedas'],
            total_leads=kpis['dolores'] + kpis['busquedas'],
            top_keywords=top_keywords
        )

        # 5. Enviar alerta de archivos generados
        if export_files:
            files_list = "\n".join([f"• {os.path.basename(f)}" for f in export_files])
            alert_system_status(
                "completado",
                f"Cierre diario exitoso\nArchivos generados:\n{files_list}"
            )
        else:
            alert_system_status("completado", "Cierre diario completado (sin datos)")

        log.info("✅ Cierre diario completado exitosamente")

    except Exception as e:
        error_msg = f"Error en cierre diario: {e}"
        log.error(error_msg)
        alert_system_status("error", error_msg)
        return False

    return True

if __name__ == "__main__":
    success = run_daily_close()
    sys.exit(0 if success else 1)
