"""Authentication configuration settings."""

import logging
import os
import secrets
from datetime import timedelta

from pydantic import Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Check if secret was provided via environment BEFORE settings load
_SECRET_KEY_PROVIDED = bool(os.environ.get("AUTH_JWT_SECRET_KEY"))


class AuthSettings(BaseSettings):
    """Authentication settings loaded from environment variables."""

    # JWT Settings
    jwt_secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT signing. Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'",
    )
    jwt_algorithm: str = Field(default="HS256", description="Algorithm for JWT signing")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiration in days"
    )

    # Password Settings
    password_min_length: int = Field(default=8, description="Minimum password length")

    # Security Settings
    max_login_attempts: int = Field(
        default=5, description="Max failed login attempts before lockout"
    )
    lockout_duration_minutes: int = Field(
        default=30, description="Account lockout duration in minutes"
    )

    # Token Settings
    token_type: str = "bearer"

    @property
    def access_token_expire_delta(self) -> timedelta:
        """Get access token expiration as timedelta."""
        return timedelta(minutes=self.access_token_expire_minutes)

    @property
    def refresh_token_expire_delta(self) -> timedelta:
        """Get refresh token expiration as timedelta."""
        return timedelta(days=self.refresh_token_expire_days)

    class Config:
        env_prefix = "AUTH_"
        env_file = ".env"
        extra = "ignore"


# Singleton instance
auth_settings = AuthSettings()


def check_jwt_secret_configuration() -> None:
    """
    Log a warning if JWT secret key was auto-generated.

    This should be called at application startup to alert operators
    that tokens will not persist across container restarts.
    """
    if not _SECRET_KEY_PROVIDED:
        logger.warning(
            "=" * 60 + "\n"
            "WARNING: AUTH_JWT_SECRET_KEY not set in environment!\n"
            "A random secret was generated. This means:\n"
            "  - All user sessions will be invalidated on restart\n"
            "  - Users will see 'Signature verification failed' errors\n"
            "\n"
            "To fix, set AUTH_JWT_SECRET_KEY in your environment:\n"
            "  python -c 'import secrets; print(secrets.token_urlsafe(32))'\n"
            "=" * 60
        )
