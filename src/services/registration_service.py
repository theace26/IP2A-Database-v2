"""User registration and email verification service."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.user import User
from src.models.email_token import EmailToken
from src.models.role import Role
from src.models.user_role import UserRole
from src.core.security import hash_password
from src.db.enums import TokenType, RoleType
from src.services.email_service import get_email_service


class RegistrationError(Exception):
    """Base exception for registration errors."""

    pass


class EmailAlreadyExistsError(RegistrationError):
    """Raised when email is already registered."""

    pass


class InvalidTokenError(RegistrationError):
    """Raised when token is invalid or expired."""

    pass


class TokenExpiredError(RegistrationError):
    """Raised when token has expired."""

    pass


# Token expiration times
VERIFICATION_TOKEN_HOURS = 24
PASSWORD_RESET_TOKEN_HOURS = 1


def _generate_token() -> tuple[str, str]:
    """Generate a secure token and its hash."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, token_hash


def _hash_token(raw_token: str) -> str:
    """Hash a token for lookup."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


async def register_user(
    db: Session,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    base_url: str,
) -> User:
    """
    Register a new user and send verification email.

    Args:
        db: Database session
        email: User's email
        password: Plain text password
        first_name: User's first name
        last_name: User's last name
        base_url: Base URL for verification link

    Returns:
        Created User object (unverified)

    Raises:
        EmailAlreadyExistsError: If email already registered
    """
    # Check if email exists
    existing = db.execute(
        select(User).where(User.email == email.lower())
    ).scalar_one_or_none()

    if existing:
        raise EmailAlreadyExistsError("Email already registered")

    # Create user (unverified)
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.flush()  # Get user ID

    # Assign default member role
    member_role = db.execute(
        select(Role).where(Role.name == RoleType.MEMBER.value)
    ).scalar_one_or_none()

    if member_role:
        user_role = UserRole(
            user_id=user.id,
            role_id=member_role.id,
            assigned_by="system",
        )
        db.add(user_role)

    # Create verification token
    raw_token, token_hash = _generate_token()
    email_token = EmailToken(
        user_id=user.id,
        token_hash=token_hash,
        token_type=TokenType.EMAIL_VERIFICATION,
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=VERIFICATION_TOKEN_HOURS),
    )
    db.add(email_token)
    db.commit()
    db.refresh(user)

    # Send verification email
    verification_url = f"{base_url}/auth/verify-email?token={raw_token}"
    email_service = get_email_service()
    await email_service.send_verification_email(
        to_email=user.email,
        user_name=user.first_name,
        verification_url=verification_url,
    )

    return user


async def verify_email(db: Session, raw_token: str) -> User:
    """
    Verify a user's email with the provided token.

    Args:
        db: Database session
        raw_token: Verification token from email link

    Returns:
        Verified User object

    Raises:
        InvalidTokenError: If token not found
        TokenExpiredError: If token has expired
    """
    token_hash = _hash_token(raw_token)

    email_token = db.execute(
        select(EmailToken).where(
            EmailToken.token_hash == token_hash,
            EmailToken.token_type == TokenType.EMAIL_VERIFICATION,
        )
    ).scalar_one_or_none()

    if not email_token:
        raise InvalidTokenError("Invalid verification token")

    if email_token.is_used:
        raise InvalidTokenError("Token has already been used")

    if email_token.is_expired:
        raise TokenExpiredError("Verification token has expired")

    # Mark token as used
    email_token.mark_used()

    # Verify user
    user = email_token.user
    user.is_verified = True

    db.commit()
    db.refresh(user)

    # Send welcome email
    email_service = get_email_service()
    await email_service.send_welcome_email(
        to_email=user.email,
        user_name=user.first_name,
    )

    return user


async def resend_verification_email(
    db: Session,
    email: str,
    base_url: str,
) -> bool:
    """
    Resend verification email to unverified user.

    Args:
        db: Database session
        email: User's email
        base_url: Base URL for verification link

    Returns:
        True if email sent, False if user not found or already verified
    """
    user = db.execute(
        select(User).where(User.email == email.lower())
    ).scalar_one_or_none()

    if not user or user.is_verified:
        # Don't reveal whether email exists
        return False

    # Invalidate old tokens
    db.execute(
        select(EmailToken).where(
            EmailToken.user_id == user.id,
            EmailToken.token_type == TokenType.EMAIL_VERIFICATION,
            ~EmailToken.is_used,
        )
    )
    for token in db.execute(
        select(EmailToken).where(
            EmailToken.user_id == user.id,
            EmailToken.token_type == TokenType.EMAIL_VERIFICATION,
            ~EmailToken.is_used,
        )
    ).scalars():
        token.is_used = True
        token.used_at = datetime.now(timezone.utc)

    # Create new token
    raw_token, token_hash = _generate_token()
    email_token = EmailToken(
        user_id=user.id,
        token_hash=token_hash,
        token_type=TokenType.EMAIL_VERIFICATION,
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=VERIFICATION_TOKEN_HOURS),
    )
    db.add(email_token)
    db.commit()

    # Send email
    verification_url = f"{base_url}/auth/verify-email?token={raw_token}"
    email_service = get_email_service()
    await email_service.send_verification_email(
        to_email=user.email,
        user_name=user.first_name,
        verification_url=verification_url,
    )

    return True


async def request_password_reset(
    db: Session,
    email: str,
    base_url: str,
) -> bool:
    """
    Request a password reset email.

    Args:
        db: Database session
        email: User's email
        base_url: Base URL for reset link

    Returns:
        True (always, to prevent email enumeration)
    """
    user = db.execute(
        select(User).where(User.email == email.lower())
    ).scalar_one_or_none()

    if not user or not user.is_active:
        # Don't reveal whether email exists
        return True

    # Invalidate old reset tokens
    for token in db.execute(
        select(EmailToken).where(
            EmailToken.user_id == user.id,
            EmailToken.token_type == TokenType.PASSWORD_RESET,
            ~EmailToken.is_used,
        )
    ).scalars():
        token.is_used = True
        token.used_at = datetime.now(timezone.utc)

    # Create reset token
    raw_token, token_hash = _generate_token()
    email_token = EmailToken(
        user_id=user.id,
        token_hash=token_hash,
        token_type=TokenType.PASSWORD_RESET,
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=PASSWORD_RESET_TOKEN_HOURS),
    )
    db.add(email_token)
    db.commit()

    # Send email
    reset_url = f"{base_url}/auth/reset-password?token={raw_token}"
    email_service = get_email_service()
    await email_service.send_password_reset_email(
        to_email=user.email,
        user_name=user.first_name,
        reset_url=reset_url,
    )

    return True


async def reset_password(
    db: Session,
    raw_token: str,
    new_password: str,
) -> User:
    """
    Reset password using a valid reset token.

    Args:
        db: Database session
        raw_token: Reset token from email
        new_password: New password

    Returns:
        Updated User object

    Raises:
        InvalidTokenError: If token not found or already used
        TokenExpiredError: If token has expired
    """
    token_hash = _hash_token(raw_token)

    email_token = db.execute(
        select(EmailToken).where(
            EmailToken.token_hash == token_hash,
            EmailToken.token_type == TokenType.PASSWORD_RESET,
        )
    ).scalar_one_or_none()

    if not email_token:
        raise InvalidTokenError("Invalid reset token")

    if email_token.is_used:
        raise InvalidTokenError("Token has already been used")

    if email_token.is_expired:
        raise TokenExpiredError("Reset token has expired")

    # Mark token as used
    email_token.mark_used()

    # Update password
    user = email_token.user
    user.password_hash = hash_password(new_password)
    user.failed_login_attempts = 0
    user.locked_until = None

    # Revoke all refresh tokens (force re-login everywhere)
    from src.services.auth_service import revoke_all_user_tokens

    revoke_all_user_tokens(db, user.id)

    db.commit()
    db.refresh(user)

    return user


def create_user_by_admin(
    db: Session,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role_names: list[str],
    is_verified: bool = True,
    member_id: Optional[int] = None,
) -> User:
    """
    Create a user as an admin (no email verification required).

    Args:
        db: Database session
        email: User's email
        password: Initial password
        first_name: User's first name
        last_name: User's last name
        role_names: List of role names to assign
        is_verified: Whether to mark as verified (default True)
        member_id: Optional link to Member record

    Returns:
        Created User object

    Raises:
        EmailAlreadyExistsError: If email already registered
    """
    # Check if email exists
    existing = db.execute(
        select(User).where(User.email == email.lower())
    ).scalar_one_or_none()

    if existing:
        raise EmailAlreadyExistsError("Email already registered")

    # Create user
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        is_active=True,
        is_verified=is_verified,
        member_id=member_id,
    )
    db.add(user)
    db.flush()

    # Assign roles
    for role_name in role_names:
        role = db.execute(
            select(Role).where(Role.name == role_name.lower())
        ).scalar_one_or_none()

        if role:
            user_role = UserRole(
                user_id=user.id,
                role_id=role.id,
                assigned_by="admin",
            )
            db.add(user_role)

    db.commit()
    db.refresh(user)

    return user
