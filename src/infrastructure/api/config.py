"""
API configuration using pydantic-settings.
Supports multiple environments: development, staging, production.
"""
from typing import Literal
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets


class Settings(BaseSettings):
    """
    FastAPI application settings.
    Loads configuration from environment variables and .env file.
    """
    
    # =====================================================================
    # ENVIRONMENT & APP INFO
    # =====================================================================
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Current environment"
    )
    APP_NAME: str = "VerifyID API"
    VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=True, description="Debug mode (auto-disabled in production)")
    
    # =====================================================================
    # API SERVER
    # =====================================================================
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    API_PREFIX: str = Field(default="/api/v1", description="API route prefix")
    
    # =====================================================================
    # DATABASE
    # =====================================================================
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/verifyid_core",
        description="PostgreSQL connection string"
    )
    DATABASE_POOL_SIZE: int = Field(default=5, description="Connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, description="Max overflow connections")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, description="Pool timeout in seconds")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, description="Recycle connections after N seconds")
    DATABASE_ECHO: bool = Field(default=False, description="Echo SQL queries (dev only)")
    
    # =====================================================================
    # SECURITY
    # =====================================================================
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT signing"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="JWT expiration (minutes)")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration (days)")
    
    # API Key settings
    API_KEY_HEADER_NAME: str = Field(default="X-API-Key", description="API key header name")
    API_KEY_PREFIX: str = Field(default="vfy_", description="API key prefix")
    API_KEY_LENGTH: int = Field(default=48, description="API key length (bytes)")
    
    # Password hashing
    BCRYPT_ROUNDS: int = Field(default=12, description="Bcrypt cost factor")
    
    # =====================================================================
    # CORS
    # =====================================================================
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials")
    CORS_ALLOW_METHODS: list[str] = Field(default=["*"], description="Allowed HTTP methods")
    CORS_ALLOW_HEADERS: list[str] = Field(default=["*"], description="Allowed HTTP headers")
    
    # =====================================================================
    # RATE LIMITING
    # =====================================================================
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Requests per minute")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, description="Requests per hour")
    
    # =====================================================================
    # LOGGING
    # =====================================================================
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or text")
    LOG_FILE: str | None = Field(default="logs/api.log", description="Log file path")
    LOG_ROTATION: str = Field(default="500 MB", description="Log rotation size")
    LOG_RETENTION: str = Field(default="10 days", description="Log retention period")
    
    # =====================================================================
    # OCR PROVIDERS (from existing config)
    # =====================================================================
    OCR_PROVIDER: str = Field(
        default="digit_ensemble",
        description="OCR provider: google_vision, azure_vision, ensemble, digit_ensemble"
    )
    
    # Google Cloud Vision
    GOOGLE_APPLICATION_CREDENTIALS: str | None = Field(
        default=None,
        description="Path to Google Cloud credentials JSON"
    )
    
    # Azure Computer Vision
    AZURE_VISION_ENDPOINT: str | None = Field(default=None, description="Azure Vision endpoint")
    AZURE_VISION_KEY: str | None = Field(default=None, description="Azure Vision API key")
    
    # =====================================================================
    # USAGE TRACKING
    # =====================================================================
    USAGE_TRACKING_ENABLED: bool = Field(default=True, description="Track API usage")
    COST_MARKUP_PERCENTAGE: float = Field(default=30.0, description="Markup % on provider costs")
    
    # =====================================================================
    # FILE UPLOAD
    # =====================================================================
    MAX_FILE_SIZE_MB: int = Field(default=10, description="Max upload file size (MB)")
    ALLOWED_FILE_TYPES: list[str] = Field(
        default=["image/jpeg", "image/png", "image/jpg", "application/pdf"],
        description="Allowed file MIME types"
    )
    
    # =====================================================================
    # VALIDATORS
    # =====================================================================
    
    @validator("DEBUG", always=True)
    def debug_auto_disable_in_production(cls, v, values):
        """Auto-disable debug in production."""
        if values.get("ENVIRONMENT") == "production":
            return False
        return v
    
    @validator("DATABASE_ECHO", always=True)
    def db_echo_only_in_dev(cls, v, values):
        """Only echo SQL in development."""
        if values.get("ENVIRONMENT") != "development":
            return False
        return v
    
    @validator("CORS_ORIGINS", always=True)
    def cors_origins_production_check(cls, v, values):
        """Prevent wildcard CORS in production."""
        if values.get("ENVIRONMENT") == "production" and "*" in v:
            raise ValueError("CORS wildcard '*' not allowed in production")
        return v
    
    @validator("SECRET_KEY", always=True)
    def secret_key_production_check(cls, v, values):
        """Require explicit SECRET_KEY in production."""
        if values.get("ENVIRONMENT") == "production" and len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters in production")
        return v
    
    # =====================================================================
    # PYDANTIC CONFIG
    # =====================================================================
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore unknown fields from .env
    )
    
    # =====================================================================
    # COMPUTED PROPERTIES
    # =====================================================================
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL (for alembic migrations)."""
        return self.DATABASE_URL.replace("+asyncpg", "").replace("+psycopg", "")


# =========================================================================
# GLOBAL SETTINGS INSTANCE
# =========================================================================

settings = Settings()


# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

def get_settings() -> Settings:
    """
    Dependency injection helper for FastAPI.
    
    Usage:
        @app.get("/config")
        def get_config(settings: Settings = Depends(get_settings)):
            return {"environment": settings.ENVIRONMENT}
    """
    return settings