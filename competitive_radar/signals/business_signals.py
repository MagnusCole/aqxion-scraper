"""
Business Signals Generator - Generador de señales de negocio

Este módulo analiza los datos procesados y genera señales
específicas de negocio accionables.
"""

import asyncio
import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class BusinessSignal:
    """Señal de negocio específica"""
    signal_type: str  # 'opportunity', 'threat', 'trend', 'alert'
    title: str
    description: str
    priority: str  # 'high', 'medium', 'low'
    confidence: float  # 0.0 to 1.0
    data: Dict[str, Any]
    timestamp: datetime

class BusinessSignalsGenerator:
    """Generador de señales de negocio accionables"""

    def __init__(self):
        self.signal_types = {
            "opportunity": self._detect_opportunities,
            "threat": self._detect_threats,
            "trend": self._detect_trends,
            "alert": self._detect_alerts
        }

    async def generate(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generar señales de negocio a partir de datos procesados

        Args:
            processed_data: Datos procesados por el DataExtractor

        Returns:
            Diccionario con señales generadas
        """
        logger.info("🎯 Generando señales de negocio...")

        signals = []
        market_analysis = processed_data.get("market_analysis", {})

        # Generar señales de cada tipo
        for signal_type, detector_func in self.signal_types.items():
            type_signals = await detector_func(market_analysis, processed_data)
            signals.extend(type_signals)

        # Ordenar por prioridad y confianza
        signals.sort(key=lambda s: (self._priority_value(s.priority), s.confidence), reverse=True)

        result = {
            "total_signals": len(signals),
            "signals_by_type": self._group_signals_by_type(signals),
            "high_priority_signals": [s for s in signals if s.priority == "high"],
            "signals": signals
        }

        logger.info(f"✅ Generadas {len(signals)} señales de negocio")
        return result

    async def _detect_opportunities(self, analysis: Dict[str, Any], processed_data: Dict[str, Any]) -> List[BusinessSignal]:
        """Detectar oportunidades de negocio"""
        signals = []

        # Oportunidad: Mercado con pocos competidores
        total_companies = analysis.get("total_companies", 0)
        if total_companies < 5:
            signals.append(BusinessSignal(
                signal_type="opportunity",
                title="Mercado con Baja Competencia",
                description=f"Solo {total_companies} competidores encontrados. Oportunidad para entrar al mercado.",
                priority="high",
                confidence=0.85,
                data={"total_companies": total_companies},
                timestamp=datetime.now()
            ))

        # Oportunidad: Servicios poco ofrecidos
        services_dist = analysis.get("services_distribution", {})
        total_services = sum(services_dist.values())

        for service, count in services_dist.items():
            coverage = count / total_services if total_services > 0 else 0
            if coverage < 0.3:  # Menos del 30% del mercado ofrece este servicio
                signals.append(BusinessSignal(
                    signal_type="opportunity",
                    title=f"Servicio Poco Ofrecido: {service.title()}",
                    description=f"Solo {count} competidores ofrecen {service}. Nicho de oportunidad.",
                    priority="medium",
                    confidence=0.75,
                    data={"service": service, "competitors": count, "coverage": coverage},
                    timestamp=datetime.now()
                ))

        # Oportunidad: Ubicaciones sin cobertura
        locations_dist = analysis.get("locations_distribution", {})
        if not locations_dist:
            signals.append(BusinessSignal(
                signal_type="opportunity",
                title="Zona Sin Cobertura Detectada",
                description="No se encontraron competidores en zonas específicas. Primera oportunidad.",
                priority="high",
                confidence=0.90,
                data={"locations_found": list(locations_dist.keys())},
                timestamp=datetime.now()
            ))

        return signals

    async def _detect_threats(self, analysis: Dict[str, Any], processed_data: Dict[str, Any]) -> List[BusinessSignal]:
        """Detectar amenazas del mercado"""
        signals = []

        # Amenaza: Alta concentración de competidores
        total_companies = analysis.get("total_companies", 0)
        if total_companies > 15:
            signals.append(BusinessSignal(
                signal_type="threat",
                title="Alta Competencia Detectada",
                description=f"{total_companies} competidores activos. Mercado saturado.",
                priority="high",
                confidence=0.80,
                data={"total_companies": total_companies},
                timestamp=datetime.now()
            ))

        # Amenaza: Competidores con precios bajos
        companies_with_prices = analysis.get("companies_with_prices", 0)
        total_companies = analysis.get("total_companies", 1)
        price_coverage = companies_with_prices / total_companies

        if price_coverage > 0.7:  # Más del 70% muestran precios
            signals.append(BusinessSignal(
                signal_type="threat",
                title="Guerra de Precios Inminente",
                description=f"{companies_with_prices} competidores muestran precios. Posible guerra de precios.",
                priority="medium",
                confidence=0.70,
                data={"companies_with_prices": companies_with_prices, "coverage": price_coverage},
                timestamp=datetime.now()
            ))

        return signals

    async def _detect_trends(self, analysis: Dict[str, Any], processed_data: Dict[str, Any]) -> List[BusinessSignal]:
        """Detectar tendencias del mercado"""
        signals = []

        # Tendencia: Servicios más demandados
        services_dist = analysis.get("services_distribution", {})
        if services_dist:
            most_popular = max(services_dist.items(), key=lambda x: x[1])
            service_name, count = most_popular

            signals.append(BusinessSignal(
                signal_type="trend",
                title=f"Tendencia: Servicio Popular - {service_name.title()}",
                description=f"{count} competidores ofrecen {service_name}. Servicio de alta demanda.",
                priority="medium",
                confidence=0.65,
                data={"service": service_name, "competitors": count},
                timestamp=datetime.now()
            ))

        # Tendencia: Ubicaciones más activas
        locations_dist = analysis.get("locations_distribution", {})
        if locations_dist:
            most_active = max(locations_dist.items(), key=lambda x: x[1])
            location_name, count = most_active

            signals.append(BusinessSignal(
                signal_type="trend",
                title=f"Tendencia: Zona Activa - {location_name}",
                description=f"{count} competidores en {location_name}. Zona de alta actividad comercial.",
                priority="low",
                confidence=0.60,
                data={"location": location_name, "competitors": count},
                timestamp=datetime.now()
            ))

        return signals

    async def _detect_alerts(self, analysis: Dict[str, Any], processed_data: Dict[str, Any]) -> List[BusinessSignal]:
        """Detectar alertas importantes"""
        signals = []

        # Alerta: Poca información de contacto
        companies_with_contact = analysis.get("companies_with_contact", 0)
        total_companies = analysis.get("total_companies", 1)
        contact_coverage = companies_with_contact / total_companies

        if contact_coverage < 0.3:  # Menos del 30% tienen contacto visible
            signals.append(BusinessSignal(
                signal_type="alert",
                title="Baja Visibilidad de Contacto",
                description=f"Solo {companies_with_contact} de {total_companies} competidores muestran contacto.",
                priority="medium",
                confidence=0.75,
                data={"companies_with_contact": companies_with_contact, "coverage": contact_coverage},
                timestamp=datetime.now()
            ))

        # Alerta: Relevancia baja promedio
        avg_relevance = analysis.get("average_relevance", 0.5)
        if avg_relevance < 0.6:
            signals.append(BusinessSignal(
                signal_type="alert",
                title="Baja Relevancia de Resultados",
                description=f"Relevancia promedio: {avg_relevance:.2f}. Posible búsqueda demasiado amplia.",
                priority="low",
                confidence=0.70,
                data={"average_relevance": avg_relevance},
                timestamp=datetime.now()
            ))

        return signals

    def _priority_value(self, priority: str) -> int:
        """Convertir prioridad a valor numérico para ordenamiento"""
        priority_map = {"high": 3, "medium": 2, "low": 1}
        return priority_map.get(priority, 0)

    def _group_signals_by_type(self, signals: List[BusinessSignal]) -> Dict[str, int]:
        """Agrupar señales por tipo"""
        grouped = {}
        for signal in signals:
            grouped[signal.signal_type] = grouped.get(signal.signal_type, 0) + 1
        return grouped
