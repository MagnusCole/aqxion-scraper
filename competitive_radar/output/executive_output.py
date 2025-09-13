"""
Executive Output Generator - Output para Consola/Telegram

Genera output de texto legible para humanos con prioridades,
acciones claras y formato ejecutivo para revisión rápida.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ExecutiveOutputGenerator:
    """Generador de output ejecutivo para humanos"""

    def __init__(self):
        self.exit_codes = {
            "no_high_priority": 0,   # Sin señales de alta prioridad
            "has_high_priority": 10  # Hay señales de alta prioridad
        }

    def generate(self, radar_data: Dict[str, Any], keyword: str) -> tuple[str, int]:
        """
        Genera output ejecutivo completo

        Args:
            radar_data: Datos del radar
            keyword: Palabra clave del escaneo

        Returns:
            Tuple de (texto_output, exit_code)
        """
        logger.info("📊 Generando output ejecutivo...")

        # Generar encabezado
        header = self._generate_header(radar_data, keyword)

        # Organizar señales por tipo y prioridad
        signals_by_type = self._organize_signals(radar_data.get("signals", []))

        # Generar secciones
        sections = []
        for signal_type, signals in signals_by_type.items():
            section = self._generate_section(signal_type, signals)
            if section:
                sections.append(section)

        # Generar resumen ejecutivo
        summary = self._generate_summary(radar_data, signals_by_type)

        # Combinar todo
        full_output = "\n".join([header] + sections + [summary])

        # Determinar código de salida
        exit_code = self._calculate_exit_code(signals_by_type)

        logger.info(f"✅ Output ejecutivo generado: {len(sections)} secciones, código {exit_code}")
        return full_output, exit_code

    def _generate_header(self, radar_data: Dict[str, Any], keyword: str) -> str:
        """Genera encabezado con metadatos"""
        now_utc = datetime.now(timezone.utc)
        lima_offset = timedelta(hours=-5)
        now_lima = now_utc + lima_offset

        # Calcular duración
        duration = radar_data.get("duration", 2.5)
        pages_scanned = radar_data.get("pages_scanned", len(radar_data.get("results", [])))
        sources = ", ".join(radar_data.get("sources", ["SERP", "Competidores"]))

        header = f"""
🛰️ COMPETITIVE RADAR - REPORTE EJECUTIVO
{'='*50}

📅 Fecha: {now_lima.strftime('%Y-%m-%d %H:%M')} Lima
🔍 Keyword: "{keyword}"
⏱️ Duración: {duration:.1f}s
📄 Páginas: {pages_scanned}
🎯 Fuentes: {sources}

🔥 Señales Críticas: {self._count_high_priority(radar_data.get('signals', []))}
📊 Total Señales: {len(radar_data.get('signals', []))}
"""
        return header.strip()

    def _organize_signals(self, signals: List[Any]) -> Dict[str, List[Any]]:
        """Organiza señales por tipo y las ordena por score"""
        organized = {
            "opportunity": [],
            "alert": [],
            "trend": []
        }

        for signal in signals:
            # Mapear tipos del sistema
            signal_type = self._map_signal_type(signal.signal_type)

            if signal_type in organized:
                organized[signal_type].append(signal)

        # Ordenar cada tipo por score (confianza)
        for signal_type in organized:
            organized[signal_type].sort(
                key=lambda s: s.confidence,
                reverse=True
            )

        return organized

    def _generate_section(self, signal_type: str, signals: List[Any]) -> str:
        """Genera una sección para un tipo de señal"""
        if not signals:
            return ""

        # Iconos y títulos por tipo
        type_config = {
            "opportunity": {"icon": "🟢", "title": "OPORTUNIDADES", "color": "verde"},
            "alert": {"icon": "🟠", "title": "ALERTAS", "color": "naranja"},
            "trend": {"icon": "🟡", "title": "TENDENCIAS", "color": "amarillo"}
        }

        config = type_config.get(signal_type, {"icon": "⚪", "title": "OTROS", "color": "gris"})

        section = f"""
{config['icon']} {config['title']} ({len(signals)})
{'-'*30}"""

        for i, signal in enumerate(signals, 1):
            priority_icon = "🚨" if signal.priority == "high" else "⚠️"
            confidence_pct = f"{signal.confidence:.1%}"

            section += f"""

{i}. {priority_icon} {signal.title}
   Confianza: {confidence_pct}
   {signal.description}

   📋 ACCIÓN: {self._generate_executive_action(signal)}

   🔍 EVIDENCIA: {self._generate_executive_evidence(signal)}"""

        return section

    def _generate_summary(self, radar_data: Dict[str, Any], signals_by_type: Dict[str, List[Any]]) -> str:
        """Genera resumen ejecutivo"""
        total_signals = sum(len(signals) for signals in signals_by_type.values())
        high_priority = self._count_high_priority(radar_data.get('signals', []))

        summary = f"""
📈 RESUMEN EJECUTIVO
{'-'*30}

🎯 Total Señales: {total_signals}
🚨 Alta Prioridad: {high_priority}

📊 Por Tipo:
"""

        for signal_type, signals in signals_by_type.items():
            if signals:
                type_name = self._get_type_display_name(signal_type)
                summary += f"   • {type_name}: {len(signals)}\n"

        # Recomendaciones basadas en señales
        recommendations = self._generate_recommendations(signals_by_type)
        if recommendations:
            summary += f"\n💡 RECOMENDACIONES:\n{recommendations}"

        return summary

    def _map_signal_type(self, signal_type: str) -> str:
        """Mapea tipos del sistema a tipos ejecutivos"""
        mapping = {
            "opportunity": "opportunity",
            "threat": "alert",
            "trend": "trend",
            "alert": "alert"
        }
        return mapping.get(signal_type, "alert")

    def _count_high_priority(self, signals: List[Any]) -> int:
        """Cuenta señales de alta prioridad"""
        return sum(1 for signal in signals if signal.priority == "high")

    def _generate_executive_action(self, signal: Any) -> str:
        """Genera acción ejecutiva concisa"""
        if signal.signal_type == "opportunity":
            if "baja competencia" in signal.title.lower():
                return "🚀 Lanzar campaña en Lima - 24h"
            elif "servicio poco ofrecido" in signal.title.lower():
                return "🎯 Desarrollar servicio especializado"
            else:
                return "💼 Evaluar entrada al mercado"

        elif signal.signal_type == "alert":
            if "visibilidad" in signal.title.lower():
                return "📱 Mejorar presencia online"
            else:
                return "🔄 Revisar estrategia actual"

        elif signal.signal_type == "trend":
            return "📈 Adaptar contenido/servicios"

        else:
            return "👀 Monitorear desarrollo"

    def _generate_executive_evidence(self, signal: Any) -> str:
        """Genera evidencia ejecutiva concisa"""
        if hasattr(signal, 'data') and signal.data:
            # Mostrar métricas clave
            metrics = []
            for key, value in signal.data.items():
                if isinstance(value, (int, float)) and value > 0:
                    metrics.append(f"{key}: {value}")

            if metrics:
                return f"📊 {' | '.join(metrics[:2])}"

        # Evidencia genérica basada en tipo
        if signal.signal_type == "opportunity":
            return "📊 Mercado con baja saturación"
        elif signal.signal_type == "alert":
            return "⚠️ Requiere atención inmediata"
        elif signal.signal_type == "trend":
            return "📈 Patrón consistente detectado"
        else:
            return "🔍 Análisis de datos disponible"

    def _get_type_display_name(self, signal_type: str) -> str:
        """Obtiene nombre display para tipo de señal"""
        names = {
            "opportunity": "Oportunidades",
            "alert": "Alertas",
            "trend": "Tendencias"
        }
        return names.get(signal_type, signal_type.title())

    def _generate_recommendations(self, signals_by_type: Dict[str, List[Any]]) -> str:
        """Genera recomendaciones basadas en señales"""
        recommendations = []

        opportunities = len(signals_by_type.get("opportunity", []))
        alerts = len(signals_by_type.get("alert", []))
        trends = len(signals_by_type.get("trend", []))

        if opportunities > 0:
            recommendations.append(f"   • {opportunities} oportunidades → Evaluar expansión")
        if alerts > 0:
            recommendations.append(f"   • {alerts} alertas → Acción correctiva")
        if trends > 0:
            recommendations.append(f"   • {trends} tendencias → Adaptar estrategia")

        return "\n".join(recommendations)

    def _calculate_exit_code(self, signals_by_type: Dict[str, List[Any]]) -> int:
        """Calcula código de salida basado en señales"""
        all_signals = []
        for signals in signals_by_type.values():
            all_signals.extend(signals)

        has_high_priority = any(signal.priority == "high" for signal in all_signals)

        return self.exit_codes["has_high_priority"] if has_high_priority else self.exit_codes["no_high_priority"]

    def print_to_console(self, output: str) -> None:
        """Imprime output a consola"""
        print(output)

    def save_to_file(self, output: str, filename: str) -> None:
        """Guarda output a archivo"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(output)
        logger.info(f"💾 Output ejecutivo guardado en: {filename}")
