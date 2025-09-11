import os
from dotenv import load_dotenv

load_dotenv()

KEYWORDS = os.getenv("KEYWORDS", "limpieza de piscina lima|agencia marketing lima|dashboard pymes peru").split("|")
MAX_PER_KW = int(os.getenv("MAX_PER_KW", "30"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
