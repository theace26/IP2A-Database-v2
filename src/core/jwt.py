"""JWT token utilities for authentication."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt

from src.config.auth_config import auth_settings


class TokenError(Exception):
    """Base exception for token-related errors."""

    pass


class TokenExpiredError(TokenError):
    """Raised when a token has expired."""

    pass


class TokenInvalidError(TokenError):
    """Raised when a token is invalid."""

    pass


def create_access_token(
    subject: str | int,
    additional_claims: Optional[dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: The subject of the token (usually user_id)
        additional_claims: Additional claims to include in the token
        expires_delta: Custom expiration time (defaults to settings)

    Returns:
        Encoded JWT token string
    """
    if expires_delta is None:
        expires_delta = auth_settings.access_token_expire_delta

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }

    if additional_claims:
        to_encode.update(additional_claims)

    return jwt.encode(
        to_encode, auth_settings.jwt_secret_key, algorithm=auth_settings.jwt_algorithm
    )


def create_refresh_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, str, datetime]:
    """
    Create a refresh token.

    Returns both the raw token (to send to client) and its hash (to store in DB).

    Args:
        subject: The subject of the token (usually user_id)
        expires_delta: Custom expiration time (defaults to settings)

    Returns:
        Tuple of (raw_token, token_hash, expires_at)
    """
    if expires_delta is None:
        expires_delta = auth_settings.refresh_token_expire_delta

    # Generate a secure random token
    raw_token = secrets.token_urlsafe(32)

    # Hash the token for storage
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    expires_at = datetime.now(timezone.utc) + expires_delta

    return raw_token, token_hash, expires_at


def verify_access_token(token: str) -> dict[str, Any]:
    """
    Verify and decode a JWT access token.

    Args:
        token: The JWT token to verify

    Returns:
        Decoded token payload

    Raises:
        TokenExpiredError: If token has expired
        TokenInvalidError: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            auth_settings.jwt_secret_key,
            algorithms=[auth_settings.jwt_algorithm],
        )

        # Verify it's an access token
        if payload.get("type") != "access":
            raise TokenInvalidError("Invalid token type")

        return payload

    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except JWTError as e:
        raise TokenInvalidError(f"Invalid token: {str(e)}")


def hash_refresh_token(raw_token: str) -> str:
    """
    Hash a refresh token for comparison.

    Args:
        raw_token: The raw refresh token from client

    Returns:
        SHA-256 hash of the token
    """
    return hashlib.sha256(raw_token.encode()).hexdigest()


def decode_token_unverified(token: str) -> dict[str, Any]:
    """
    Decode a token without verification (for debugging/logging).

    WARNING: Do not use this for authentication decisions.

    Args:
        token: The JWT token to decode

    Returns:
        Decoded token payload (unverified)
    """
    return jwt.decode(
        token,
        auth_settings.jwt_secret_key,
        algorithms=[auth_settings.jwt_algorithm],
        options={"verify_signature": False},
    )
