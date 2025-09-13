"""
Storage Module - Almacenamiento y gestión de datos

Este módulo maneja el almacenamiento específico del radar:
- Market Data: Esquemas de datos del mercado
- Signal History: Historial de señales generadas
"""

from .market_data import MarketDataStorage

__all__ = ["MarketDataStorage"]
