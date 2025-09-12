"""
Modern configuration system using Pydantic for validation and type safety.
Replaces the old environment variable approach with a robust configuration system.
"""

from pathlib import Path
from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pydantic.types import SecretStr

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class ScrapingSettings(BaseSettings):
    """Settings for web scraping operations"""

    # Keywords for scraping
    keywords: List[str] = Field(
        default=[
            "agencia marketing digital",
            "consultoria marketing",
            "marketing digital peru",
            "empresa marketing lima",
            "servicios marketing digital",
            "marketing online peru",
            "agencia publicidad lima",
            "marketing digital empresa",
            "consultor marketing digital",
            "marketing digital negocios",
            "pyme marketing lima",
            "marketing digital pequeno negocio",
            "empresa marketing pequeno",
            "marketing digital startup",
            "consultoria marketing pequeno negocio"
        ],
        description="Keywords to search for business opportunities"
    )

    # Scraping limits
    max_per_keyword: int = Field(default=10, ge=1, le=100, description="Maximum posts per keyword")
    max_concurrent_requests: int = Field(default=5, ge=1, le=20, description="Maximum concurrent HTTP requests")

    # Rate limiting - Optimizado para mejor rendimiento
    domain_rate_limit: float = Field(default=0.2, ge=0.05, le=2.0, description="Seconds between requests to same domain (optimized)")
    max_backoff_delay: int = Field(default=60, ge=5, le=600, description="Maximum backoff delay in seconds (increased)")

    # Token bucket settings - Nuevo sistema avanzado
    token_bucket_burst_capacity: int = Field(default=15, ge=5, le=50, description="Maximum tokens in burst capacity")
    token_bucket_refill_rate: float = Field(default=3.0, ge=0.5, le=10.0, description="Tokens refilled per second")
    token_bucket_jitter_min: float = Field(default=0.05, ge=0.01, le=0.5, description="Minimum jitter delay")
    token_bucket_jitter_max: float = Field(default=0.3, ge=0.1, le=1.0, description="Maximum jitter delay")

    # Domain-specific overrides - Configuración granular por dominio
    sensitive_domain_burst: int = Field(default=3, ge=1, le=10, description="Burst capacity for sensitive domains")
    sensitive_domain_rate: float = Field(default=0.5, ge=0.1, le=2.0, description="Refill rate for sensitive domains")
    normal_domain_burst: int = Field(default=12, ge=5, le=30, description="Burst capacity for normal domains")
    normal_domain_rate: float = Field(default=2.5, ge=0.5, le=8.0, description="Refill rate for normal domains")

    # Content filtering
    min_title_length: int = Field(default=15, ge=5, le=100, description="Minimum title length to process")
    min_content_length: int = Field(default=20, ge=10, le=200, description="Minimum content length to process")

    # Quality thresholds
    min_relevance_score: int = Field(default=70, ge=0, le=150, description="Minimum relevance score for alerts")
    high_value_threshold: int = Field(default=80, ge=0, le=150, description="Threshold for high-value lead alerts")

    # Search engine settings
    search_engine: str = Field(default="google", pattern=r"^(google|duckduckgo|mock)$", description="Search engine to use")
    google_api_key: Optional[str] = Field(default=None, description="Google Custom Search API key")
    google_cse_id: Optional[str] = Field(default=None, description="Google Custom Search Engine ID")
    search_results_per_keyword: int = Field(default=10, ge=1, le=50, description="Number of search results per keyword")

    class Config:
        env_prefix = "SCRAPING_"
        case_sensitive = False


class OpenAISettings(BaseSettings):
    """OpenAI API configuration for AI-powered features"""

    # API Configuration
    api_key: Optional[SecretStr] = Field(default=None, description="OpenAI API key")
    base_url: str = Field(default="https://api.openai.com/v1", description="OpenAI API base URL")

    # Model Configuration
    model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")
    embedding_model: str = Field(default="text-embedding-3-small", description="Model for embeddings")

    # Feature Flags
    enable_keyword_generation: bool = Field(default=True, description="Enable AI-powered keyword generation")
    enable_content_classification: bool = Field(default=True, description="Enable AI-powered content classification")
    enable_relevance_scoring: bool = Field(default=False, description="Enable AI-powered relevance scoring")

    # Rate Limiting
    requests_per_minute: int = Field(default=50, ge=1, le=200, description="Maximum requests per minute")
    max_tokens_per_request: int = Field(default=1000, ge=100, le=4000, description="Maximum tokens per request")

    # Caching
    cache_ttl: int = Field(default=3600, ge=300, le=86400, description="TTL for AI response cache")

    # Fallback Settings
    fallback_to_regex: bool = Field(default=True, description="Fallback to regex classification if AI fails")

    class Config:
        env_prefix = "OPENAI_"
        case_sensitive = False


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""

    path: Path = Field(default=Path("scraping.db"), description="Path to SQLite database")
    enable_wal: bool = Field(default=True, description="Enable WAL mode for better concurrency")
    synchronous_mode: str = Field(default="NORMAL", pattern=r"^(FULL|NORMAL|OFF)$", description="SQLite synchronous mode")
    cache_size: int = Field(default=-64000, description="SQLite cache size in KB (negative for KB)")
    journal_mode: str = Field(default="WAL", pattern=r"^(DELETE|TRUNCATE|PERSIST|MEMORY|WAL|OFF)$", description="SQLite journal mode")

    # Connection pool settings
    max_connections: int = Field(default=10, ge=1, le=100, description="Maximum database connections")
    connection_timeout: float = Field(default=30.0, ge=1.0, le=300.0, description="Connection timeout in seconds")

    class Config:
        env_prefix = "DB_"
        case_sensitive = False


class AlertSettings(BaseSettings):
    """Alert system configuration"""

    # Telegram settings
    telegram_token: Optional[SecretStr] = Field(default=None, description="Telegram bot token")
    telegram_chat_id: Optional[str] = Field(default=None, description="Telegram chat ID for alerts")

    # Alert thresholds
    enable_high_value_alerts: bool = Field(default=True, description="Enable alerts for high-value leads")
    enable_system_alerts: bool = Field(default=True, description="Enable system status alerts")
    enable_daily_summary: bool = Field(default=True, description="Enable daily summary alerts")

    # Rate limiting for alerts
    alert_cooldown_seconds: int = Field(default=300, ge=60, le=3600, description="Minimum seconds between similar alerts")

    class Config:
        env_prefix = "ALERT_"
        case_sensitive = False


class CacheSettings(BaseSettings):
    """Caching system configuration"""

    # Redis settings
    redis_url: Optional[str] = Field(default=None, description="Redis URL for distributed caching")
    redis_ttl: int = Field(default=3600, ge=300, le=86400, description="Default TTL for cached items")

    # Local cache settings
    local_cache_size: int = Field(default=10000, ge=1000, le=100000, description="Local cache maximum size")
    local_cache_ttl: int = Field(default=3600, ge=300, le=86400, description="Local cache TTL")

    # Cache keys
    enable_url_cache: bool = Field(default=True, description="Cache scraped URLs")
    enable_content_cache: bool = Field(default=True, description="Cache processed content")
    enable_intent_cache: bool = Field(default=True, description="Cache intent analysis results")

    class Config:
        env_prefix = "CACHE_"
        case_sensitive = False


class ExportSettings(BaseSettings):
    """Export system configuration"""

    # Output settings
    output_directory: Path = Field(default=Path("exports"), description="Directory for exported files")
    enable_csv_export: bool = Field(default=True, description="Enable CSV export")
    enable_json_export: bool = Field(default=True, description="Enable JSON export")

    # Google Sheets integration
    google_sheets_url: Optional[str] = Field(default=None, description="Google Sheets URL for export")
    google_credentials_path: Optional[Path] = Field(default=None, description="Path to Google credentials")

    # Export scheduling
    daily_export_hour: int = Field(default=6, ge=0, le=23, description="Hour to run daily export (UTC)")
    enable_auto_export: bool = Field(default=True, description="Enable automatic daily exports")

    class Config:
        env_prefix = "EXPORT_"
        case_sensitive = False


class MonitoringSettings(BaseSettings):
    """Monitoring and observability settings"""

    # Logging
    log_level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s %(name)s %(levelname)s %(message)s",
        description="Log format string"
    )
    enable_structured_logging: bool = Field(default=False, description="Enable structured JSON logging")

    # Metrics
    enable_prometheus: bool = Field(default=False, description="Enable Prometheus metrics")
    prometheus_port: int = Field(default=8000, ge=1024, le=65535, description="Prometheus metrics port")

    # Health checks
    enable_health_checks: bool = Field(default=True, description="Enable health check endpoints")
    health_check_interval: int = Field(default=60, ge=10, le=300, description="Health check interval in seconds")

    class Config:
        env_prefix = "MONITORING_"
        case_sensitive = False


class MLSettings(BaseSettings):
    """Machine Learning settings for intent analysis"""

    # Model settings
    enable_ml_intent_analysis: bool = Field(default=False, description="Enable ML-based intent analysis")
    model_name: str = Field(default="facebook/bart-large-mnli", description="HuggingFace model name")
    model_cache_dir: Optional[Path] = Field(default=None, description="Directory to cache ML models")

    # Processing settings
    batch_size: int = Field(default=16, ge=1, le=64, description="Batch size for ML processing")
    max_sequence_length: int = Field(default=512, ge=128, le=1024, description="Maximum sequence length")

    # Confidence thresholds
    confidence_threshold: float = Field(default=0.7, ge=0.1, le=1.0, description="Minimum confidence for predictions")

    class Config:
        env_prefix = "ML_"
        case_sensitive = False


class Settings(BaseSettings):
    """Main application settings"""

    # Core settings
    app_name: str = Field(default="Aqxion Scraper", description="Application name")
    version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Sub-settings
    scraping: ScrapingSettings = ScrapingSettings()
    openai: OpenAISettings = OpenAISettings()
    database: DatabaseSettings = DatabaseSettings()
    alerts: AlertSettings = AlertSettings()
    cache: CacheSettings = CacheSettings()
    export: ExportSettings = ExportSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    ml: MLSettings = MLSettings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    @field_validator("debug", mode="before")
    @classmethod
    def validate_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment"""
    global settings
    settings = Settings()
    return settings


# Convenience functions for backward compatibility
def get_keywords() -> List[str]:
    """Get keywords list (backward compatibility)"""
    return settings.scraping.keywords


def get_max_per_kw() -> int:
    """Get max posts per keyword (backward compatibility)"""
    return settings.scraping.max_per_keyword


def get_log_level() -> str:
    """Get log level (backward compatibility)"""
    return settings.monitoring.log_level


def get_db_path() -> Path:
    """Get database path (backward compatibility)"""
    return settings.database.path


def get_domain_rate_limit() -> float:
    """Get domain rate limit (backward compatibility)"""
    return settings.scraping.domain_rate_limit
