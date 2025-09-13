"""
Market Radar - Sistema Nervioso del Mercado

Un sistema inteligente que convierte datos dispersos del internet
en inteligencia accionable sobre el mercado.

Módulos principales:
- sensors: Motores de búsqueda y extracción de datos
- processors: Procesamiento inteligente de información
- signals: Generador de señales de negocio
- storage: Almacenamiento y gestión de datos
- dashboard: Panel de control e informes
"""

from .cli import main

__version__ = "0.1.0"
__author__ = "Aqxion Team"

__all__ = ["main"]
