"""
Market Radar Configuration

Configuración específica del Market Radar
"""

# Configuración de sensores
SENSOR_CONFIG = {
    "google_search": {
        "max_results": 20,
        "timeout": 30,
        "user_agent": "MarketRadar/1.0"
    },
    "google_reviews": {
        "max_reviews": 50,
        "timeout": 20
    }
}

# Configuración de procesamiento
PROCESSING_CONFIG = {
    "min_relevance_threshold": 0.5,
    "max_concurrent_requests": 5,
    "extraction_timeout": 10
}

# Configuración de señales
SIGNALS_CONFIG = {
    "opportunity_threshold": 0.7,
    "threat_threshold": 0.8,
    "min_confidence_display": 0.6
}

# Configuración de almacenamiento
STORAGE_CONFIG = {
    "retention_days": 90,
    "cleanup_interval_hours": 24,
    "max_scans_history": 1000
}
