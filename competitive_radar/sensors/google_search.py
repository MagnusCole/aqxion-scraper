"""
Google Search Sensor - Sensor de búsqueda en Google

Este sensor busca competidores y oportunidades en Google Search.
Utiliza técnicas de búsqueda inteligente para encontrar información relevante.
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

class GoogleSearchSensor:
    """Sensor especializado en búsqueda de Google"""

    def __init__(self):
        self.search_engines = {
            "google": "https://www.google.com/search",
            "google_peru": "https://www.google.com.pe/search"
        }

    async def search(self, keyword: str, limit: int = 10, region: str = "peru") -> List[Dict[str, Any]]:
        """
        Buscar información en Google

        Args:
            keyword: Palabra clave para búsqueda
            limit: Número máximo de resultados
            region: Región de búsqueda (peru, global)

        Returns:
            Lista de resultados encontrados
        """
        logger.info(f"🔍 Buscando en Google: '{keyword}' (límite: {limit})")

        # Por ahora, simular resultados hasta implementar scraping real
        results = await self._mock_search(keyword, limit)

        logger.info(f"📊 Encontrados {len(results)} resultados relevantes")
        return results

    async def _mock_search(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """Simulación de búsqueda (hasta implementar scraping real)"""
        # Simular algunos resultados típicos para limpieza de piscina
        mock_results = [
            {
                "title": "Limpieza de Piscinas Lima - Servicio Profesional",
                "url": "https://limpiezapiscinaslima.com",
                "snippet": "Servicio profesional de limpieza y mantenimiento de piscinas en Lima. Precios competitivos, atención 24/7.",
                "domain": "limpiezapiscinaslima.com",
                "relevance_score": 0.95
            },
            {
                "title": "Pool Clean Lima - Limpieza Piscinas",
                "url": "https://poolcleanlima.pe",
                "snippet": "Especialistas en limpieza de piscinas residenciales y comerciales. Tratamiento químico incluido.",
                "domain": "poolcleanlima.pe",
                "relevance_score": 0.88
            },
            {
                "title": "Servicio de Mantenimiento Piscinas Miraflores",
                "url": "https://piscinas-miraflores.com",
                "snippet": "Mantenimiento completo de piscinas en Miraflores. Limpieza, filtrado, cloración.",
                "domain": "piscinas-miraflores.com",
                "relevance_score": 0.82
            }
        ]

        # Filtrar por límite y keyword
        filtered_results = []
        for result in mock_results[:limit]:
            if self._is_relevant_result(result, keyword):
                filtered_results.append(result)

        return filtered_results

    def _is_relevant_result(self, result: Dict[str, Any], keyword: str) -> bool:
        """Verificar si un resultado es relevante para la búsqueda"""
        keyword_lower = keyword.lower()

        # Verificar si el keyword aparece en título o snippet
        title_match = keyword_lower in result["title"].lower()
        snippet_match = keyword_lower in result["snippet"].lower()

        # Verificar términos relacionados
        related_terms = ["piscina", "pool", "limpieza", "mantenimiento", "servicio"]
        has_related_term = any(term in result["title"].lower() or term in result["snippet"].lower()
                              for term in related_terms)

        return title_match or snippet_match or has_related_term

    async def get_competitor_urls(self, keyword: str, max_urls: int = 20) -> List[str]:
        """Obtener URLs de competidores"""
        results = await self.search(keyword, limit=max_urls)
        return [result["url"] for result in results]

    def extract_domain(self, url: str) -> str:
        """Extraer dominio de una URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return url

    def filter_business_urls(self, urls: List[str]) -> List[str]:
        """Filtrar URLs que parecen ser de negocios"""
        business_indicators = [
            ".com", ".pe", ".net",
            "servicio", "empresa", "business",
            "pool", "piscina", "clean"
        ]

        filtered = []
        for url in urls:
            url_lower = url.lower()
            if any(indicator in url_lower for indicator in business_indicators):
                filtered.append(url)

        return filtered
