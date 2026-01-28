"""Authentication configuration settings."""

import secrets
from datetime import timedelta

from pydantic import Field
from pydantic_settings import BaseSettings


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
