"""
JSON Output Generator - Output para Automatización

Genera output JSON machine-readable con evidencia completa
para integración con sistemas automatizados.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class SignalData:
    """Estructura de datos para una señal"""
    signal_type: str  # "Opportunity", "Alert", "Trend"
    priority: str     # "high", "normal"
    score: float      # 0-100
    title: str
    description: str
    evidence_urls: List[str]
    metrics: Dict[str, Any]
    action: str
    rule_id: str

@dataclass
class RunMetadata:
    """Metadatos del run de radar"""
    run_id: str
    run_utc: str
    run_local_lima: str
    version: str
    keyword: str
    duration: float
    pages_scanned: int
    sources: List[str]

@dataclass
class RunKPIs:
    """KPIs agregados del run"""
    signals_total: int
    high_priority: int
    opportunities: int
    alerts: int
    trends: int

class JSONOutputGenerator:
    """Generador de output JSON para automatización"""

    def __init__(self, version: str = "1.0.0"):
        self.version = version

    def generate(self, radar_data: Dict[str, Any], keyword: str) -> str:
        """
        Genera output JSON completo

        Args:
            radar_data: Datos del radar (señales, análisis, etc.)
            keyword: Palabra clave del escaneo

        Returns:
            JSON string formateado
        """
        logger.info("📊 Generando output JSON...")

        # Generar metadatos del run
        metadata = self._generate_metadata(keyword, radar_data)

        # Convertir señales al formato JSON
        signals = self._convert_signals(radar_data.get("signals", []))

        # Calcular KPIs
        kpis = self._calculate_kpis(signals)

        # Crear estructura final
        output_data = {
            "run_id": metadata.run_id,
            "run_utc": metadata.run_utc,
            "run_local_lima": metadata.run_local_lima,
            "version": metadata.version,
            "keyword": metadata.keyword,
            "duration": metadata.duration,
            "pages_scanned": metadata.pages_scanned,
            "sources": metadata.sources,
            "signals": [asdict(signal) for signal in signals],
            "kpis": asdict(kpis)
        }

        # Convertir a JSON con formato legible
        json_output = json.dumps(output_data, indent=2, ensure_ascii=False)

        logger.info(f"✅ Output JSON generado: {len(signals)} señales, {len(json_output)} caracteres")
        return json_output

    def _generate_metadata(self, keyword: str, radar_data: Dict[str, Any]) -> RunMetadata:
        """Genera metadatos del run"""
        now_utc = datetime.now(timezone.utc)
        lima_offset = timedelta(hours=-5)  # UTC-5
        now_lima = now_utc + lima_offset

        run_id = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Estimar duración (por ahora simulada)
        duration = radar_data.get("duration", 2.5)

        # Estimar páginas escaneadas
        pages_scanned = radar_data.get("pages_scanned", len(radar_data.get("results", [])))

        # Fuentes utilizadas
        sources = radar_data.get("sources", ["SERP", "Competidores"])

        return RunMetadata(
            run_id=run_id,
            run_utc=now_utc.isoformat(),
            run_local_lima=now_lima.isoformat(),
            version=self.version,
            keyword=keyword,
            duration=duration,
            pages_scanned=pages_scanned,
            sources=sources
        )

    def _convert_signals(self, signals_data: List[Any]) -> List[SignalData]:
        """Convierte señales del sistema al formato JSON"""
        converted_signals = []

        for signal in signals_data:
            # Convertir tipos del sistema a tipos JSON
            signal_type = self._map_signal_type(signal.signal_type)
            priority = "high" if signal.priority == "high" else "normal"
            score = int(signal.confidence * 100)  # Convertir 0.85 a 85

            # Generar rule_id basado en el tipo y contenido
            rule_id = self._generate_rule_id(signal)

            # Crear evidencia URLs (simuladas por ahora)
            evidence_urls = self._generate_evidence_urls(signal)

            # Extraer métricas
            metrics = signal.data if hasattr(signal, 'data') and signal.data else {}

            # Generar acción recomendada
            action = self._generate_action(signal)

            signal_data = SignalData(
                signal_type=signal_type,
                priority=priority,
                score=score,
                title=signal.title,
                description=signal.description,
                evidence_urls=evidence_urls,
                metrics=metrics,
                action=action,
                rule_id=rule_id
            )

            converted_signals.append(signal_data)

        return converted_signals

    def _map_signal_type(self, signal_type: str) -> str:
        """Mapea tipos de señal del sistema a tipos JSON"""
        type_mapping = {
            "opportunity": "Opportunity",
            "threat": "Alert",
            "trend": "Trend",
            "alert": "Alert"
        }
        return type_mapping.get(signal_type, "Alert")

    def _generate_rule_id(self, signal: Any) -> str:
        """Genera un rule_id basado en el tipo y contenido de la señal"""
        signal_type = signal.signal_type.lower()
        title_slug = signal.title.lower().replace(" ", "_").replace("(", "").replace(")", "")

        # Crear rule_id determinístico
        return f"{signal_type}.{title_slug}.v1"

    def _generate_evidence_urls(self, signal: Any) -> List[str]:
        """Genera URLs de evidencia (simuladas por ahora)"""
        # En un sistema real, estas vendrían de los datos de scraping
        base_urls = [
            "https://competidor1.pe",
            "https://competidor2.com",
            "https://competidor3.pe"
        ]

        # Retornar subset basado en el tipo de señal
        if signal.signal_type == "opportunity":
            return base_urls[:3]
        elif signal.signal_type == "alert":
            return base_urls[1:3]
        else:
            return base_urls[:2]

    def _generate_action(self, signal: Any) -> str:
        """Genera acción recomendada basada en la señal"""
        if signal.signal_type == "opportunity":
            if "baja competencia" in signal.title.lower():
                return "Crear landing Lima (24h) con CTA WhatsApp."
            elif "servicio poco ofrecido" in signal.title.lower():
                return "Desarrollar oferta especializada en este servicio."
            else:
                return "Evaluar entrada en este segmento de mercado."

        elif signal.signal_type == "alert":
            if "visibilidad" in signal.title.lower():
                return "Mejorar presencia online y datos de contacto."
            else:
                return "Revisar y ajustar estrategia actual."

        elif signal.signal_type == "trend":
            return "Adaptar contenido y servicios a esta tendencia."

        else:
            return "Monitorear desarrollo de esta señal."

    def _calculate_kpis(self, signals: List[SignalData]) -> RunKPIs:
        """Calcula KPIs agregados del run"""
        total_signals = len(signals)
        high_priority = sum(1 for s in signals if s.priority == "high")

        opportunities = sum(1 for s in signals if s.signal_type == "Opportunity")
        alerts = sum(1 for s in signals if s.signal_type == "Alert")
        trends = sum(1 for s in signals if s.signal_type == "Trend")

        return RunKPIs(
            signals_total=total_signals,
            high_priority=high_priority,
            opportunities=opportunities,
            alerts=alerts,
            trends=trends
        )

    def save_to_file(self, json_output: str, filename: str) -> None:
        """Guarda el output JSON a archivo"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(json_output)
        logger.info(f"💾 Output JSON guardado en: {filename}")
