"""
HoloHub Configuration Module

Centralized configuration management using Pydantic Settings.
All environment variables are loaded and validated at startup.
"""
import secrets
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(origins: List[str]) -> List[str]:
    """Parse CORS origins from environment variable."""
    if "*" in origins:
        return ["*"]
    return origins


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -----------------------------------------------------------------------------
    # Application
    # -----------------------------------------------------------------------------
    app_name: str = Field(default="HoloHub", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # -----------------------------------------------------------------------------
    # Database
    # -----------------------------------------------------------------------------
    database_url: str = Field(alias="DATABASE_URL")
    db_pool_size: int = Field(default=20, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    db_pool_recycle: int = Field(default=3600, alias="DB_POOL_RECYCLE")

    # Test database (optional)
    test_database_url: Optional[str] = Field(default=None, alias="TEST_DATABASE_URL")

    # -----------------------------------------------------------------------------
    # Redis
    # -----------------------------------------------------------------------------
    redis_url: str = Field(alias="REDIS_URL")
    redis_decode_responses: bool = Field(default=True, alias="REDIS_DECODE_RESPONSES")

    # Test redis (optional)
    test_redis_url: Optional[str] = Field(default=None, alias="TEST_REDIS_URL")

    # -----------------------------------------------------------------------------
    # Security
    # -----------------------------------------------------------------------------
    secret_key: str = Field(
        default_factory=lambda: secrets.token_hex(32),
        alias="SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # Password requirements
    password_min_length: int = Field(default=12, alias="PASSWORD_MIN_LENGTH")
    password_require_uppercase: bool = Field(default=True, alias="PASSWORD_REQUIRE_UPPERCASE")
    password_require_lowercase: bool = Field(default=True, alias="PASSWORD_REQUIRE_LOWERCASE")
    password_require_digit: bool = Field(default=True, alias="PASSWORD_REQUIRE_DIGIT")
    password_require_special: bool = Field(default=True, alias="PASSWORD_REQUIRE_SPECIAL")

    # MFA encryption
    mfa_encryption_key: str = Field(
        default_factory=lambda: secrets.token_hex(32),
        alias="MFA_ENCRYPTION_KEY",
    )

    # Account lockout
    max_login_attempts: int = Field(default=5, alias="MAX_LOGIN_ATTEMPTS")
    account_lockout_minutes: int = Field(default=15, alias="ACCOUNT_LOCKOUT_MINUTES")

    # -----------------------------------------------------------------------------
    # S3/MinIO Storage
    # -----------------------------------------------------------------------------
    s3_endpoint: str = Field(alias="S3_ENDPOINT")
    s3_access_key: str = Field(alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(alias="S3_SECRET_KEY")
    s3_bucket: str = Field(alias="S3_BUCKET")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    s3_use_ssl: bool = Field(default=False, alias="S3_USE_SSL")

    # Asset settings
    max_upload_size_mb: int = Field(default=500, alias="MAX_UPLOAD_SIZE_MB")
    allowed_file_extensions: str = Field(
        default=".glb,.gltf,.obj,.fbx,.usdz",
        alias="ALLOWED_FILE_EXTENSIONS",
    )

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get allowed file extensions as a list."""
        return [ext.strip() for ext in self.allowed_file_extensions.split(",")]

    # -----------------------------------------------------------------------------
    # CORS
    # -----------------------------------------------------------------------------
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        alias="CORS_ORIGINS",
    )
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        alias="CORS_ALLOW_METHODS",
    )
    cors_allow_headers: List[str] = Field(default=["*"], alias="CORS_ALLOW_HEADERS")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # -----------------------------------------------------------------------------
    # Rate Limiting
    # -----------------------------------------------------------------------------
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_storage_uri: str = Field(default="redis://localhost:6379/1", alias="RATE_LIMIT_STORAGE_URI")

    # -----------------------------------------------------------------------------
    # Celery
    # -----------------------------------------------------------------------------
    celery_broker_url: str = Field(alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(alias="CELERY_RESULT_BACKEND")
    celery_task_tracked: bool = Field(default=True, alias="CELERY_TASK_TRACKED")
    celery_task_time_limit: int = Field(default=3600, alias="CELERY_TASK_TIME_LIMIT")
    celery_task_soft_time_limit: int = Field(default=3000, alias="CELERY_TASK_SOFT_TIME_LIMIT")

    # -----------------------------------------------------------------------------
    # Logging
    # -----------------------------------------------------------------------------
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # -----------------------------------------------------------------------------
    # TimescaleDB
    # -----------------------------------------------------------------------------
    timescaledb_enabled: bool = Field(default=True, alias="TIMESCALEDB_ENABLED")
    timescaledb_retention_days: int = Field(default=90, alias="TIMESCALEDB_RETENTION_DAYS")

    # -----------------------------------------------------------------------------
    # Monitoring
    # -----------------------------------------------------------------------------
    # Sentry
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    sentry_traces_sample_rate: float = Field(default=0.1, alias="SENTRY_TRACES_SAMPLE_RATE")
    sentry_profiles_sample_rate: float = Field(default=0.1, alias="SENTRY_PROFILES_SAMPLE_RATE")

    # Prometheus
    metrics_enabled: bool = Field(default=True, alias="METRICS_ENABLED")
    metrics_path: str = Field(default="/metrics", alias="METRICS_PATH")

    # OpenTelemetry
    otel_service_name: str = Field(default="holohub-api", alias="OTEL_SERVICE_NAME")
    otel_exporter_otlp_endpoint: Optional[str] = Field(default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    otel_traces_sampler: str = Field(default="parentbased_traceidratio", alias="OTEL_TRACES_SAMPLER")
    otel_traces_sampler_arg: float = Field(default=0.1, alias="OTEL_TRACES_SAMPLER_ARG")

    # -----------------------------------------------------------------------------
    # Email
    # -----------------------------------------------------------------------------
    smtp_host: Optional[str] = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, alias="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="noreply@holohub.com", alias="SMTP_FROM")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")

    # -----------------------------------------------------------------------------
    # Stripe (Billing)
    # -----------------------------------------------------------------------------
    stripe_api_key: Optional[str] = Field(default=None, alias="STRIPE_API_KEY")
    stripe_webhook_secret: Optional[str] = Field(default=None, alias="STRIPE_WEBHOOK_SECRET")
    stripe_price_id_pro: Optional[str] = Field(default=None, alias="STRIPE_PRICE_ID_PRO")
    stripe_price_id_enterprise: Optional[str] = Field(default=None, alias="STRIPE_PRICE_ID_ENTERPRISE")

    # -----------------------------------------------------------------------------
    # CDN (CloudFront)
    # -----------------------------------------------------------------------------
    cloudfront_domain: Optional[str] = Field(default=None, alias="CLOUDFRONT_DOMAIN")
    cloudfront_key_id: Optional[str] = Field(default=None, alias="CLOUDFRONT_KEY_ID")
    cloudfront_private_key_path: Optional[str] = Field(default=None, alias="CLOUDFRONT_PRIVATE_KEY_PATH")
    cloudfront_url_expiration_hours: int = Field(default=8760, alias="CLOUDFRONT_URL_EXPIRATION_HOURS")

    # -----------------------------------------------------------------------------
    # WebSocket
    # -----------------------------------------------------------------------------
    websocket_heartbeat_interval: int = Field(default=30, alias="WEBSOCKET_HEARTBEAT_INTERVAL")
    websocket_max_connections: int = Field(default=10000, alias="WEBSOCKET_MAX_CONNECTIONS")
    websocket_message_queue_size: int = Field(default=100, alias="WEBSOCKET_MESSAGE_QUEUE_SIZE")

    # -----------------------------------------------------------------------------
    # Device Settings
    # -----------------------------------------------------------------------------
    device_token_expire_days: int = Field(default=30, alias="DEVICE_TOKEN_EXPIRE_DAYS")
    device_activation_code_length: int = Field(default=9, alias="DEVICE_ACTIVATION_CODE_LENGTH")
    device_offline_threshold_minutes: int = Field(default=5, alias="DEVICE_OFFLINE_THRESHOLD_MINUTES")
    device_offline_auto_decommission_days: int = Field(default=30, alias="DEVICE_OFFLINE_AUTO_DECOMMISSION_DAYS")

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        """Validate application environment."""
        valid_envs = ["development", "staging", "production", "test"]
        if v not in valid_envs:
            raise ValueError(f"app_env must be one of {valid_envs}")
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    This function uses lru_cache to ensure settings are loaded only once
    and then reused for subsequent calls. This is important for performance
    and to avoid re-reading environment variables on every call.
    """
    return Settings()
