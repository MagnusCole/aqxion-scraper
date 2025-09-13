"""
Sensors Module - Motores de búsqueda y extracción

Este módulo contiene todos los sensores que escuchan al mercado:
- Google Search: Búsqueda orgánica de competidores
- Google Reviews: Extracción de reseñas y opiniones
- Forums: Monitoreo de foros y comunidades
- Marketplaces: Seguimiento de precios y ofertas
"""

from .google_search import GoogleSearchSensor

__all__ = ["GoogleSearchSensor"]
