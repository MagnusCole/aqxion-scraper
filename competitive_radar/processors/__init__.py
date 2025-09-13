"""
Processors Module - Procesamiento inteligente de datos

Este módulo procesa los datos crudos del mercado:
- Data Extractor: Extracción inteligente de información
- Sentiment Analyzer: Análisis básico de sentimiento
- Pattern Detector: Detección de patrones y tendencias
"""

from .data_extractor import DataExtractor

__all__ = ["DataExtractor"]
