"""
Signals Module - Generador de señales de negocio

Este módulo transforma datos en señales accionables:
- Business Signals: Señales específicas de negocio
- Opportunity Detector: Detector de oportunidades
- Alert System: Sistema de alertas inteligentes
"""

from .business_signals import BusinessSignalsGenerator

__all__ = ["BusinessSignalsGenerator"]
