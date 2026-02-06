"""Application settings with environment-based configuration."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    IP2A_ENV: str = "dev"  # dev | test | prod (legacy)

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ip2a"
    TEST_DATABASE_URL: Optional[str] = None

    # Security
    SECRET_KEY: str = "change-me-in-production-min-32-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    ALLOWED_HOSTS: str = "*"

    # S3 Storage
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BUCKET_NAME: str = "ip2a-documents"
    S3_REGION: str = "us-east-1"

    # Database Pool Settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800  # 30 minutes
    DB_ECHO: bool = False

    # Monitoring & Error Tracking
    SENTRY_DSN: Optional[str] = None
    APP_VERSION: str = "0.9.1-alpha"

    # CORS (production)
    ALLOWED_ORIGINS: Optional[str] = None

    # Feature flags
    ENABLE_DOCS: bool = True  # Swagger UI
    JSON_LOGS: bool = True  # Structured JSON logging in production

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cors_origins(self) -> list[str]:
        if self.ALLOWED_HOSTS == "*":
            return ["*"]
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",")]

    @property
    def database_url(self) -> str:
        """Get database URL, handling Railway's postgres:// format."""
        url = self.DATABASE_URL
        # Handle Railway's postgres:// vs postgresql://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
