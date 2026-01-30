"""Authentication service for login, logout, and token management."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from src.models.user import User
from src.models.refresh_token import RefreshToken
from src.core.security import hash_password, verify_password
from src.core.jwt import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)
from src.config.auth_config import auth_settings
from src.services.user_service import get_user_by_email, get_user


class AuthenticationError(Exception):
    """Base exception for authentication errors."""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""

    pass


class AccountLockedError(AuthenticationError):
    """Raised when account is locked."""

    pass


class AccountInactiveError(AuthenticationError):
    """Raised when account is inactive."""

    pass


class TokenRevokedError(AuthenticationError):
    """Raised when refresh token has been revoked."""

    pass


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Authenticate a user by email and password.

    Args:
        db: Database session
        email: User's email
        password: Plain text password

    Returns:
        Authenticated User object

    Raises:
        InvalidCredentialsError: If email/password invalid
        AccountLockedError: If account is locked
        AccountInactiveError: If account is inactive
    """
    user = get_user_by_email(db, email)

    if not user:
        # Use same error to prevent email enumeration
        raise InvalidCredentialsError("Invalid email or password")

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise AccountLockedError(
            f"Account is locked until {user.locked_until.isoformat()}"
        )

    # Check if account is active
    if not user.is_active:
        raise AccountInactiveError("Account is inactive")

    # Verify password
    if not verify_password(password, user.password_hash):
        # Increment failed attempts
        user.failed_login_attempts += 1

        # Check if should lock
        if user.failed_login_attempts >= auth_settings.max_login_attempts:
            from datetime import timedelta

            user.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=auth_settings.lockout_duration_minutes
            )

        db.commit()
        raise InvalidCredentialsError("Invalid email or password")

    # Successful login - reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    return user


def create_tokens(
    db: Session,
    user: User,
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> dict:
    """
    Create access and refresh tokens for a user.

    Args:
        db: Database session
        user: Authenticated user
        device_info: Optional device information
        ip_address: Optional IP address

    Returns:
        Dict with access_token, refresh_token, token_type, expires_in
    """
    # Create access token with user info
    access_token = create_access_token(
        subject=user.id,
        additional_claims={
            "email": user.email,
            "roles": user.role_names,
            "must_change_password": user.must_change_password,
        },
    )

    # Create refresh token
    raw_refresh_token, token_hash, expires_at = create_refresh_token(user.id)

    # Store refresh token in database
    db_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        device_info=device_info,
        ip_address=ip_address,
    )
    db.add(db_token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh_token,
        "token_type": auth_settings.token_type,
        "expires_in": auth_settings.access_token_expire_minutes * 60,
    }


def refresh_access_token(
    db: Session,
    raw_refresh_token: str,
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> dict:
    """
    Refresh an access token using a refresh token.

    Implements token rotation - old refresh token is revoked,
    new refresh token is issued.

    Args:
        db: Database session
        raw_refresh_token: The refresh token from client
        device_info: Optional device information
        ip_address: Optional IP address

    Returns:
        Dict with new access_token, refresh_token, token_type, expires_in

    Raises:
        TokenRevokedError: If token is revoked or invalid
    """
    # Hash the token to look up in database
    token_hash = hash_refresh_token(raw_refresh_token)

    # Find the token
    db_token = (
        db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    )

    if not db_token:
        raise TokenRevokedError("Invalid refresh token")

    if db_token.is_revoked:
        raise TokenRevokedError("Refresh token has been revoked")

    if db_token.is_expired:
        raise TokenRevokedError("Refresh token has expired")

    # Get the user
    user = get_user(db, db_token.user_id)
    if not user or not user.is_active:
        raise TokenRevokedError("User not found or inactive")

    # Revoke the old token (token rotation)
    db_token.is_revoked = True
    db_token.revoked_at = datetime.now(timezone.utc)

    # Create new tokens
    return create_tokens(db, user, device_info, ip_address)


def revoke_refresh_token(db: Session, raw_refresh_token: str) -> bool:
    """
    Revoke a specific refresh token (logout from one device).

    Args:
        db: Database session
        raw_refresh_token: The refresh token to revoke

    Returns:
        True if token was revoked, False if not found
    """
    token_hash = hash_refresh_token(raw_refresh_token)

    db_token = (
        db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    )

    if not db_token:
        return False

    db_token.is_revoked = True
    db_token.revoked_at = datetime.now(timezone.utc)
    db.commit()

    return True


def revoke_all_user_tokens(db: Session, user_id: int) -> int:
    """
    Revoke all refresh tokens for a user (logout from all devices).

    Args:
        db: Database session
        user_id: The user's ID

    Returns:
        Number of tokens revoked
    """
    now = datetime.now(timezone.utc)

    result = (
        db.query(RefreshToken)
        .filter(RefreshToken.user_id == user_id, ~RefreshToken.is_revoked)
        .update({"is_revoked": True, "revoked_at": now})
    )

    db.commit()
    return result


def change_password(
    db: Session, user: User, current_password: str, new_password: str
) -> bool:
    """
    Change a user's password.

    Args:
        db: Database session
        user: The user changing password
        current_password: Current password for verification
        new_password: New password to set

    Returns:
        True if successful

    Raises:
        InvalidCredentialsError: If current password is wrong
    """
    if not verify_password(current_password, user.password_hash):
        raise InvalidCredentialsError("Current password is incorrect")

    user.password_hash = hash_password(new_password)

    # Revoke all tokens (force re-login)
    revoke_all_user_tokens(db, user.id)

    db.commit()
    return True


def cleanup_expired_tokens(db: Session) -> int:
    """
    Delete expired refresh tokens from database.

    Should be run periodically (e.g., daily cron job).

    Args:
        db: Database session

    Returns:
        Number of tokens deleted
    """
    now = datetime.now(timezone.utc)

    result = db.query(RefreshToken).filter(RefreshToken.expires_at < now).delete()

    db.commit()
    return result
