"""
Output Module - Generadores de Output Múltiple

Este módulo proporciona tres tipos de output para diferentes usos:

1. JSON: Para automatización (machine-readable con evidencia)
2. CSV: Para analítica/CRM/Sheets (fácil de revisar y compartir)
3. Texto Ejecutivo: Para consola/Telegram (prioridades y acciones)
"""

from .json_output import JSONOutputGenerator
from .csv_output import CSVOutputGenerator
from .executive_output import ExecutiveOutputGenerator

__all__ = ["JSONOutputGenerator", "CSVOutputGenerator", "ExecutiveOutputGenerator"]
