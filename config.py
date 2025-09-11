import os
from typing import List, Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# === CONFIGURACIÓN DE ALERTAS ===
TELEGRAM_TOKEN: Optional[str] = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: Optional[str] = os.getenv('TELEGRAM_CHAT_ID')

# === CONFIGURACIÓN DE SCRAPING ===
LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
MAX_PER_KW: int = int(os.getenv('MAX_PER_KW', '10'))

# Keywords para scraping - expandidas para mejor cobertura
KEYWORDS: List[str] = os.getenv(
    "KEYWORDS",
    "agencia marketing digital|consultoria marketing|marketing digital peru|empresa marketing lima|servicios marketing digital|marketing online peru|agencia publicidad lima|marketing digital empresa|consultor marketing digital|marketing digital negocios|pyme marketing lima|marketing digital pequeno negocio|empresa marketing pequeno|marketing digital startup|consultoria marketing pequeno negocio"
).split("|")

# === CONFIGURACIÓN DE BASE DE DATOS ===
DB_PATH: str = os.getenv('DB_PATH', 'scraping.db')

# === CONFIGURACIÓN DE RATE LIMITING ===
DOMAIN_RATE_LIMIT: float = float(os.getenv('DOMAIN_RATE_LIMIT', '0.5'))

# === CONFIGURACIÓN DE EXPORTACIÓN ===
GOOGLE_SHEETS_URL: Optional[str] = os.getenv('GOOGLE_SHEETS_URL')
GOOGLE_SHEETS_CREDENTIALS_PATH: Optional[str] = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')

# === CONFIGURACIÓN DE WHATSAPP (FUTURA IMPLEMENTACIÓN) ===
WHATSAPP_API_URL: Optional[str] = os.getenv('WHATSAPP_API_URL')
WHATSAPP_ACCESS_TOKEN: Optional[str] = os.getenv('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_PHONE_NUMBER_ID: Optional[str] = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
