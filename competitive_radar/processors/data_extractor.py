"""
Data Extractor - Procesador inteligente de datos

Este procesador extrae información relevante de los datos crudos
obtenidos por los sensores del mercado.
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExtractedData:
    """Datos extraídos de una fuente"""
    title: str
    description: str
    services: List[str]
    location: Optional[str]
    price_info: Optional[str]
    contact_info: Optional[str]
    relevance_score: float

class DataExtractor:
    """Extractor inteligente de datos del mercado"""

    def __init__(self):
        self.service_keywords = {
            "limpieza": ["limpieza", "clean", "limpiar", "lavar"],
            "mantenimiento": ["mantenimiento", "maintenance", "reparación", "reparar"],
            "tratamiento": ["tratamiento", "químico", "cloro", "ph", "filtrado"],
            "instalación": ["instalación", "install", "montaje", "construcción"],
            "reparación": ["reparación", "reparar", "arreglar", "fix"]
        }

        self.location_keywords = [
            "lima", "miraflores", "san isidro", "surco", "barranco",
            "jesús maría", "lince", "pueblo libre", "magdalena"
        ]

    async def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesar datos crudos y extraer información relevante

        Args:
            raw_data: Datos crudos del sensor

        Returns:
            Datos procesados con información extraída
        """
        logger.info("🧠 Procesando datos crudos...")

        sensor_type = raw_data.get("sensor", "unknown")
        results = raw_data.get("results", [])

        processed_results = []
        for result in results:
            extracted = await self._extract_from_result(result)
            if extracted:
                processed_results.append(extracted)

        # Análisis agregado
        analysis = self._analyze_dataset(processed_results)

        processed_data = {
            "sensor_type": sensor_type,
            "total_results": len(results),
            "processed_results": len(processed_results),
            "extracted_data": processed_results,
            "market_analysis": analysis
        }

        logger.info(f"✅ Procesados {len(processed_results)} resultados de {len(results)}")
        return processed_data

    async def _extract_from_result(self, result: Dict[str, Any]) -> Optional[ExtractedData]:
        """Extraer información de un resultado individual"""
        try:
            title = result.get("title", "")
            snippet = result.get("snippet", "")

            # Combinar título y snippet para análisis
            full_text = f"{title} {snippet}".lower()

            # Extraer servicios
            services = self._extract_services(full_text)

            # Extraer ubicación
            location = self._extract_location(full_text)

            # Extraer información de precios
            price_info = self._extract_price_info(full_text)

            # Extraer información de contacto
            contact_info = self._extract_contact_info(full_text)

            # Calcular relevancia
            relevance_score = self._calculate_relevance(result, services, location)

            return ExtractedData(
                title=title,
                description=snippet,
                services=services,
                location=location,
                price_info=price_info,
                contact_info=contact_info,
                relevance_score=relevance_score
            )

        except Exception as e:
            logger.warning(f"Error procesando resultado: {e}")
            return None

    def _extract_services(self, text: str) -> List[str]:
        """Extraer servicios mencionados en el texto"""
        services_found = []

        for service_type, keywords in self.service_keywords.items():
            if any(keyword in text for keyword in keywords):
                services_found.append(service_type)

        return list(set(services_found))  # Eliminar duplicados

    def _extract_location(self, text: str) -> Optional[str]:
        """Extraer ubicación del texto"""
        for location in self.location_keywords:
            if location in text:
                return location.title()  # Capitalizar
        return None

    def _extract_price_info(self, text: str) -> Optional[str]:
        """Extraer información de precios"""
        # Buscar patrones de precios comunes en Perú
        price_patterns = [
            r's/[\d,]+',  # S/ 100, S/50
            r'\$[\d,]+',  # $100, $50
            r'[\d,]+\s*soles',  # 100 soles
            r'precio[\w\s]*:?\s*[\d,]+'  # precio: 100
        ]

        for pattern in price_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return ", ".join(matches[:3])  # Máximo 3 matches

        return None

    def _extract_contact_info(self, text: str) -> Optional[str]:
        """Extraer información de contacto"""
        # Buscar teléfonos peruanos
        phone_pattern = r'9\d{2}[\s\-]\d{3}[\s\-]\d{3}'
        phones = re.findall(phone_pattern, text)

        if phones:
            return ", ".join(phones[:2])  # Máximo 2 teléfonos

        return None

    def _calculate_relevance(self, result: Dict[str, Any], services: List[str], location: Optional[str]) -> float:
        """Calcular puntuación de relevancia"""
        base_score = result.get("relevance_score", 0.5)

        # Bonus por servicios encontrados
        service_bonus = len(services) * 0.1

        # Bonus por ubicación específica
        location_bonus = 0.2 if location else 0.0

        # Calcular score final
        final_score = min(base_score + service_bonus + location_bonus, 1.0)

        return round(final_score, 2)

    def _analyze_dataset(self, extracted_data: List[ExtractedData]) -> Dict[str, Any]:
        """Analizar el conjunto de datos extraídos"""
        if not extracted_data:
            return {"error": "No hay datos para analizar"}

        # Análisis de servicios
        all_services = []
        for data in extracted_data:
            all_services.extend(data.services)

        service_counts = {}
        for service in all_services:
            service_counts[service] = service_counts.get(service, 0) + 1

        # Análisis de ubicaciones
        locations = [data.location for data in extracted_data if data.location]
        location_counts = {}
        for location in locations:
            location_counts[location] = location_counts.get(location, 0) + 1

        # Estadísticas generales
        avg_relevance = sum(data.relevance_score for data in extracted_data) / len(extracted_data)

        return {
            "total_companies": len(extracted_data),
            "services_distribution": service_counts,
            "locations_distribution": location_counts,
            "average_relevance": round(avg_relevance, 2),
            "companies_with_prices": sum(1 for data in extracted_data if data.price_info),
            "companies_with_contact": sum(1 for data in extracted_data if data.contact_info)
        }
