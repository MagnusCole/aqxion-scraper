"""
Signal Dashboard - Panel de control de señales

Este módulo presenta las señales de negocio de manera clara
y organizada para toma de decisiones.
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class SignalDashboard:
    """Dashboard para visualizar señales de negocio"""

    def __init__(self):
        self.colors = {
            "opportunity": "🟢",
            "threat": "🔴",
            "trend": "🟡",
            "alert": "🟠"
        }

        self.priority_icons = {
            "high": "🚨",
            "medium": "⚠️",
            "low": "ℹ️"
        }

    async def display(self, signals_data: Dict[str, Any]) -> None:
        """
        Mostrar dashboard completo de señales

        Args:
            signals_data: Datos de señales generadas
        """
        logger.info("📊 Generando dashboard de señales...")

        print("\n" + "="*80)
        print("📡 MARKET RADAR - SISTEMA NERVIOSO DEL MERCADO")
        print("="*80)

        # Resumen general
        await self._display_summary(signals_data)

        # Señales de alta prioridad
        await self._display_high_priority_signals(signals_data)

        # Señales por tipo
        await self._display_signals_by_type(signals_data)

        # Recomendaciones
        await self._display_recommendations(signals_data)

        print("\n" + "="*80)
        print("🎯 Fin del reporte - Market Radar")
        print("="*80)

    async def _display_summary(self, signals_data: Dict[str, Any]) -> None:
        """Mostrar resumen general"""
        total_signals = signals_data.get("total_signals", 0)
        signals_by_type = signals_data.get("signals_by_type", {})
        high_priority = len(signals_data.get("high_priority_signals", []))

        print(f"\n📊 RESUMEN GENERAL")
        print(f"   Señales Totales: {total_signals}")
        print(f"   Alta Prioridad: {high_priority}")

        if signals_by_type:
            print(f"   Por Tipo:")
            for signal_type, count in signals_by_type.items():
                icon = self.colors.get(signal_type, "⚪")
                print(f"     {icon} {signal_type.title()}: {count}")

    async def _display_high_priority_signals(self, signals_data: Dict[str, Any]) -> None:
        """Mostrar señales de alta prioridad"""
        high_priority_signals = signals_data.get("high_priority_signals", [])

        if not high_priority_signals:
            print(f"\n🚨 SEÑALES DE ALTA PRIORIDAD")
            print(f"   ✅ No hay señales críticas en este momento")
            return

        print(f"\n🚨 SEÑALES DE ALTA PRIORIDAD ({len(high_priority_signals)})")

        for i, signal in enumerate(high_priority_signals, 1):
            icon = self.colors.get(signal.signal_type, "⚪")
            priority_icon = self.priority_icons.get(signal.priority, "❓")

            print(f"\n   {i}. {icon} {priority_icon} {signal.title}")
            print(f"      {signal.description}")
            print(f"      Confianza: {signal.confidence:.1%}")

            # Mostrar datos adicionales si existen
            if signal.data:
                print(f"      Datos: {signal.data}")

    async def _display_signals_by_type(self, signals_data: Dict[str, Any]) -> None:
        """Mostrar señales agrupadas por tipo"""
        signals = signals_data.get("signals", [])

        if not signals:
            return

        # Agrupar por tipo
        by_type = {}
        for signal in signals:
            signal_type = signal.signal_type
            if signal_type not in by_type:
                by_type[signal_type] = []
            by_type[signal_type].append(signal)

        # Mostrar cada tipo
        for signal_type, type_signals in by_type.items():
            icon = self.colors.get(signal_type, "⚪")
            print(f"\n{icon} SEÑALES DE {signal_type.upper()} ({len(type_signals)})")

            for signal in type_signals:
                priority_icon = self.priority_icons.get(signal.priority, "❓")
                confidence_pct = f"{signal.confidence:.1%}"

                print(f"   • {priority_icon} {signal.title} ({confidence_pct})")
                print(f"     {signal.description}")

    async def _display_recommendations(self, signals_data: Dict[str, Any]) -> None:
        """Mostrar recomendaciones basadas en las señales"""
        signals = signals_data.get("signals", [])
        signals_by_type = signals_data.get("signals_by_type", {})

        print(f"\n💡 RECOMENDACIONES ESTRATÉGICAS")

        # Recomendaciones basadas en oportunidades
        opportunities = signals_by_type.get("opportunity", 0)
        if opportunities > 0:
            print(f"   🟢 OPORTUNIDADES: {opportunities} señales detectadas")
            print(f"      → Considerar expansión en nichos identificados")
            print(f"      → Evaluar entrada en mercados con baja competencia")

        # Recomendaciones basadas en amenazas
        threats = signals_by_type.get("threat", 0)
        if threats > 0:
            print(f"   🔴 AMENAZAS: {threats} señales detectadas")
            print(f"      → Monitorear movimientos de competidores")
            print(f"      → Preparar estrategias de diferenciación")

        # Recomendaciones basadas en tendencias
        trends = signals_by_type.get("trend", 0)
        if trends > 0:
            print(f"   🟡 TENDENCIAS: {trends} señales detectadas")
            print(f"      → Adaptar servicios a demandas del mercado")
            print(f"      → Considerar expansión en zonas activas")

        # Recomendaciones generales
        total_signals = signals_data.get("total_signals", 0)
        if total_signals == 0:
            print(f"   ✅ MERCADO ESTABLE")
            print(f"      → Continuar monitoreo regular")
            print(f"      → Mantener estrategias actuales")
        elif total_signals > 5:
            print(f"   ⚡ MERCADO DINÁMICO")
            print(f"      → Aumentar frecuencia de monitoreo")
            print(f"      → Preparar planes de contingencia")

    def format_signal_for_display(self, signal) -> str:
        """Formatear una señal para display"""
        icon = self.colors.get(signal.signal_type, "⚪")
        priority_icon = self.priority_icons.get(signal.priority, "❓")

        return f"{icon} {priority_icon} {signal.title} ({signal.confidence:.1%})"

    def export_signals_report(self, signals_data: Dict[str, Any], filename: str) -> None:
        """Exportar reporte de señales a archivo"""
        # TODO: Implementar exportación a archivo
        pass
