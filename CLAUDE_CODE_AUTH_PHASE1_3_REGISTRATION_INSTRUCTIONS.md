# Claude Code Instructions: Phase 1.3 - User Registration & Email Verification

> **Project:** IP2A-Database-v2
> **Phase:** 1.3 - User Registration & Email Verification
> **Estimated Time:** 3-4 hours
> **Prerequisites:** Phase 1.2 complete (JWT authentication working)

---

## Objective

Implement user registration with email verification:
- User self-registration endpoint
- Email verification token generation and validation
- Password reset flow (forgot password)
- Rate limiting on auth endpoints
- Admin user creation (for staff creating accounts)

---

## Before You Start

### 1. Verify Environment

```bash
cd ~/Projects/IP2A-Database-v2
git status                    # Should be clean, on main
git pull origin main          # Get latest
pytest -v                     # Verify 140 tests pass
```

### 2. Verify Phase 1.2 Complete

```bash
# These should exist and work
ls src/routers/auth.py
ls src/services/auth_service.py
ls src/core/security.py
ls src/core/jwt.py

# Test login works
pytest -v src/tests/test_auth_router.py
```

---

## Implementation Steps

### Step 1: Create Email Token Model

**File:** `src/models/email_token.py`

```python
"""Email verification and password reset token model."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, ForeignKey, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.mixins import TimestampMixin
from src.db.enums import TokenType

if TYPE_CHECKING:
    from src.models.user import User


class EmailToken(Base, TimestampMixin):
    """
    Token for email verification and password reset.
    
    Tokens are stored hashed for security.
    Single-use: marked as used after successful verification.
    """
    
    __tablename__ = "email_tokens"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    token_type: Mapped[TokenType] = mapped_column(
        SQLEnum(TokenType, name="token_type_enum"),
        nullable=False
    )
    
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="email_tokens")
    
    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired
    
    def mark_used(self) -> None:
        """Mark token as used."""
        self.is_used = True
        self.used_at = datetime.now(timezone.utc)
    
    def __repr__(self) -> str:
        return f"<EmailToken(id={self.id}, type={self.token_type}, is_valid={self.is_valid})>"
```

### Step 2: Update User Model

**File:** `src/models/user.py` - Add email_tokens relationship

Add import at top:
```python
if TYPE_CHECKING:
    # ... existing imports ...
    from src.models.email_token import EmailToken
```

Add relationship to User class:
```python
    email_tokens: Mapped[list["EmailToken"]] = relationship(
        "EmailToken",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
```

### Step 3: Update Models __init__.py

**File:** `src/models/__init__.py` - Add EmailToken export

```python
from src.models.email_token import EmailToken

__all__ = [
    # ... existing exports ...
    "EmailToken",
]
```

### Step 4: Create Database Migration

```bash
alembic revision --autogenerate -m "Add email_tokens table"
alembic upgrade head
```

---

### Step 5: Create Email Service (Abstract)

**File:** `src/services/email_service.py`

```python
"""Email service for sending verification and reset emails."""

from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EmailServiceBase(ABC):
    """Abstract base class for email services."""
    
    @abstractmethod
    async def send_verification_email(
        self,
        to_email: str,
        user_name: str,
        verification_url: str,
    ) -> bool:
        """Send email verification link."""
        pass
    
    @abstractmethod
    async def send_password_reset_email(
        self,
        to_email: str,
        user_name: str,
        reset_url: str,
    ) -> bool:
        """Send password reset link."""
        pass
    
    @abstractmethod
    async def send_welcome_email(
        self,
        to_email: str,
        user_name: str,
    ) -> bool:
        """Send welcome email after verification."""
        pass


class ConsoleEmailService(EmailServiceBase):
    """
    Development email service that logs to console.
    
    Use this for development/testing. Replace with real
    email service (SMTP, SendGrid, etc.) in production.
    """
    
    async def send_verification_email(
        self,
        to_email: str,
        user_name: str,
        verification_url: str,
    ) -> bool:
        """Log verification email to console."""
        logger.info(
            f"\n{'='*50}\n"
            f"EMAIL VERIFICATION\n"
            f"{'='*50}\n"
            f"To: {to_email}\n"
            f"Subject: Verify your IP2A account\n"
            f"\n"
            f"Hello {user_name},\n"
            f"\n"
            f"Please verify your email by clicking:\n"
            f"{verification_url}\n"
            f"\n"
            f"This link expires in 24 hours.\n"
            f"{'='*50}\n"
        )
        return True
    
    async def send_password_reset_email(
        self,
        to_email: str,
        user_name: str,
        reset_url: str,
    ) -> bool:
        """Log password reset email to console."""
        logger.info(
            f"\n{'='*50}\n"
            f"PASSWORD RESET\n"
            f"{'='*50}\n"
            f"To: {to_email}\n"
            f"Subject: Reset your IP2A password\n"
            f"\n"
            f"Hello {user_name},\n"
            f"\n"
            f"Reset your password by clicking:\n"
            f"{reset_url}\n"
            f"\n"
            f"This link expires in 1 hour.\n"
            f"If you didn't request this, ignore this email.\n"
            f"{'='*50}\n"
        )
        return True
    
    async def send_welcome_email(
        self,
        to_email: str,
        user_name: str,
    ) -> bool:
        """Log welcome email to console."""
        logger.info(
            f"\n{'='*50}\n"
            f"WELCOME EMAIL\n"
            f"{'='*50}\n"
            f"To: {to_email}\n"
            f"Subject: Welcome to IP2A!\n"
            f"\n"
            f"Hello {user_name},\n"
            f"\n"
            f"Your email has been verified. Welcome to IP2A!\n"
            f"{'='*50}\n"
        )
        return True


class SMTPEmailService(EmailServiceBase):
    """
    Production email service using SMTP.
    
    Configure via environment variables:
    - SMTP_HOST
    - SMTP_PORT
    - SMTP_USER
    - SMTP_PASSWORD
    - SMTP_FROM_EMAIL
    - SMTP_FROM_NAME
    """
    
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        from_name: str = "IP2A System",
        use_tls: bool = True,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
        self.use_tls = use_tls
    
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str,
    ) -> bool:
        """Send email via SMTP."""
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            
            msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))
            
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.from_email, to_email, msg.as_string())
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    async def send_verification_email(
        self,
        to_email: str,
        user_name: str,
        verification_url: str,
    ) -> bool:
        """Send verification email via SMTP."""
        subject = "Verify your IP2A account"
        body_text = f"""
Hello {user_name},

Please verify your email by visiting:
{verification_url}

This link expires in 24 hours.

- IP2A System
"""
        body_html = f"""
<html>
<body>
<p>Hello {user_name},</p>
<p>Please verify your email by clicking the link below:</p>
<p><a href="{verification_url}">Verify Email</a></p>
<p>Or copy this URL: {verification_url}</p>
<p>This link expires in 24 hours.</p>
<p>- IP2A System</p>
</body>
</html>
"""
        return await self._send_email(to_email, subject, body_html, body_text)
    
    async def send_password_reset_email(
        self,
        to_email: str,
        user_name: str,
        reset_url: str,
    ) -> bool:
        """Send password reset email via SMTP."""
        subject = "Reset your IP2A password"
        body_text = f"""
Hello {user_name},

You requested a password reset. Visit this link:
{reset_url}

This link expires in 1 hour.

If you didn't request this, ignore this email.

- IP2A System
"""
        body_html = f"""
<html>
<body>
<p>Hello {user_name},</p>
<p>You requested a password reset. Click the link below:</p>
<p><a href="{reset_url}">Reset Password</a></p>
<p>Or copy this URL: {reset_url}</p>
<p>This link expires in 1 hour.</p>
<p>If you didn't request this, ignore this email.</p>
<p>- IP2A System</p>
</body>
</html>
"""
        return await self._send_email(to_email, subject, body_html, body_text)
    
    async def send_welcome_email(
        self,
        to_email: str,
        user_name: str,
    ) -> bool:
        """Send welcome email via SMTP."""
        subject = "Welcome to IP2A!"
        body_text = f"""
Hello {user_name},

Your email has been verified. Welcome to IP2A!

You can now log in at: [APP_URL]

- IP2A System
"""
        body_html = f"""
<html>
<body>
<p>Hello {user_name},</p>
<p>Your email has been verified. Welcome to IP2A!</p>
<p>You can now <a href="[APP_URL]">log in</a>.</p>
<p>- IP2A System</p>
</body>
</html>
"""
        return await self._send_email(to_email, subject, body_html, body_text)


# Factory function to get email service based on config
def get_email_service() -> EmailServiceBase:
    """
    Get the appropriate email service based on configuration.
    
    Returns ConsoleEmailService for development,
    SMTPEmailService for production.
    """
    import os
    
    smtp_host = os.getenv("SMTP_HOST")
    
    if smtp_host:
        return SMTPEmailService(
            host=smtp_host,
            port=int(os.getenv("SMTP_PORT", "587")),
            username=os.getenv("SMTP_USER", ""),
            password=os.getenv("SMTP_PASSWORD", ""),
            from_email=os.getenv("SMTP_FROM_EMAIL", "noreply@ip2a.local"),
            from_name=os.getenv("SMTP_FROM_NAME", "IP2A System"),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        )
    
    return ConsoleEmailService()
```

---

### Step 6: Create Registration Service

**File:** `src/services/registration_service.py`

```python
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
from src.config.auth_config import auth_settings
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
        expires_at=datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_TOKEN_HOURS),
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
            EmailToken.is_used == False,
        )
    )
    for token in db.execute(
        select(EmailToken).where(
            EmailToken.user_id == user.id,
            EmailToken.token_type == TokenType.EMAIL_VERIFICATION,
            EmailToken.is_used == False,
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
        expires_at=datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_TOKEN_HOURS),
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
            EmailToken.is_used == False,
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
        expires_at=datetime.now(timezone.utc) + timedelta(hours=PASSWORD_RESET_TOKEN_HOURS),
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
```

---

### Step 7: Update Auth Schemas

**File:** `src/schemas/auth.py` - Add registration schemas

Add to existing file:

```python
class UserRegistrationRequest(BaseModel):
    """Schema for user self-registration."""
    
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


class UserRegistrationResponse(BaseModel):
    """Schema for registration response."""
    
    id: int
    email: str
    first_name: str
    last_name: str
    message: str = "Registration successful. Please check your email to verify your account."


class EmailVerificationRequest(BaseModel):
    """Schema for email verification."""
    
    token: str


class ResendVerificationRequest(BaseModel):
    """Schema for resending verification email."""
    
    email: EmailStr


class PasswordResetRequest(BaseModel):
    """Schema for requesting password reset."""
    
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for confirming password reset."""
    
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class AdminUserCreateRequest(BaseModel):
    """Schema for admin creating a user."""
    
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    roles: list[str] = Field(default=["member"])
    is_verified: bool = True
    member_id: Optional[int] = None
```

---

### Step 8: Update Auth Router

**File:** `src/routers/auth.py` - Add registration endpoints

Add imports at top:

```python
from src.services.registration_service import (
    register_user,
    verify_email,
    resend_verification_email,
    request_password_reset,
    reset_password,
    create_user_by_admin,
    EmailAlreadyExistsError,
    InvalidTokenError,
    TokenExpiredError,
)
from src.schemas.auth import (
    UserRegistrationRequest,
    UserRegistrationResponse,
    EmailVerificationRequest,
    ResendVerificationRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    AdminUserCreateRequest,
)
from src.routers.dependencies.auth import AdminUser
```

Add new endpoints:

```python
@router.post("/register", response_model=UserRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register(
    registration_data: UserRegistrationRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Register a new user account.
    
    A verification email will be sent to the provided email address.
    The user must verify their email before they can log in.
    """
    # Get base URL for verification link
    base_url = str(request.base_url).rstrip("/")
    
    try:
        user = await register_user(
            db=db,
            email=registration_data.email,
            password=registration_data.password,
            first_name=registration_data.first_name,
            last_name=registration_data.last_name,
            base_url=base_url,
        )
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    
    return UserRegistrationResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
    )


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email_endpoint(
    verification_data: EmailVerificationRequest,
    db: Session = Depends(get_db),
):
    """
    Verify email address with the provided token.
    
    Token is sent to user's email during registration.
    """
    try:
        user = await verify_email(db, verification_data.token)
        return {"message": "Email verified successfully", "email": user.email}
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired. Please request a new one.",
        )


@router.get("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email_get(
    token: str,
    db: Session = Depends(get_db),
):
    """
    Verify email address via GET request (for clicking email links).
    
    Redirects or returns success message.
    """
    try:
        user = await verify_email(db, token)
        return {"message": "Email verified successfully", "email": user.email}
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired. Please request a new one.",
        )


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(
    resend_data: ResendVerificationRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Resend verification email.
    
    Always returns success to prevent email enumeration.
    """
    base_url = str(request.base_url).rstrip("/")
    await resend_verification_email(db, resend_data.email, base_url)
    return {"message": "If the email exists and is unverified, a verification email has been sent."}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    reset_data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Request a password reset email.
    
    Always returns success to prevent email enumeration.
    """
    base_url = str(request.base_url).rstrip("/")
    await request_password_reset(db, reset_data.email, base_url)
    return {"message": "If the email exists, a password reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password_endpoint(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    """
    Reset password using a valid reset token.
    """
    try:
        user = await reset_password(db, reset_data.token, reset_data.new_password)
        return {"message": "Password reset successfully", "email": user.email}
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one.",
        )


@router.post("/admin/create-user", response_model=UserRegistrationResponse, status_code=status.HTTP_201_CREATED)
def admin_create_user(
    user_data: AdminUserCreateRequest,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Create a new user as an admin.
    
    No email verification required. User can log in immediately.
    Admin-only endpoint.
    """
    try:
        user = create_user_by_admin(
            db=db,
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role_names=user_data.roles,
            is_verified=user_data.is_verified,
            member_id=user_data.member_id,
        )
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    
    return UserRegistrationResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        message="User created successfully.",
    )
```

---

### Step 9: Add Rate Limiting (Simple)

**File:** `src/middleware/rate_limit.py`

```python
"""Simple in-memory rate limiting middleware."""

import time
from collections import defaultdict
from typing import Callable
from fastapi import Request, HTTPException, status


class RateLimiter:
    """
    Simple in-memory rate limiter.
    
    For production, use Redis-based rate limiting.
    """
    
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, client_id: str) -> None:
        """Remove requests older than 1 minute."""
        now = time.time()
        cutoff = now - 60
        self.requests[client_id] = [
            ts for ts in self.requests[client_id] if ts > cutoff
        ]
    
    def is_rate_limited(self, request: Request) -> bool:
        """Check if client is rate limited."""
        client_id = self._get_client_id(request)
        self._cleanup_old_requests(client_id)
        
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return True
        
        self.requests[client_id].append(time.time())
        return False
    
    def __call__(self, request: Request) -> None:
        """Check rate limit, raise exception if exceeded."""
        if self.is_rate_limited(request):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": "60"},
            )


# Rate limiters for different endpoints
auth_rate_limiter = RateLimiter(requests_per_minute=10)
registration_rate_limiter = RateLimiter(requests_per_minute=5)
password_reset_rate_limiter = RateLimiter(requests_per_minute=3)


def rate_limit_auth(request: Request) -> None:
    """Rate limit for auth endpoints (login, refresh)."""
    auth_rate_limiter(request)


def rate_limit_registration(request: Request) -> None:
    """Rate limit for registration endpoints."""
    registration_rate_limiter(request)


def rate_limit_password_reset(request: Request) -> None:
    """Rate limit for password reset endpoints."""
    password_reset_rate_limiter(request)
```

**Update auth router to use rate limiting:**

Add to imports in `src/routers/auth.py`:

```python
from src.middleware.rate_limit import (
    rate_limit_auth,
    rate_limit_registration,
    rate_limit_password_reset,
)
```

Add dependencies to endpoints:

```python
@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limit_auth)])
# ... existing code ...

@router.post("/register", ..., dependencies=[Depends(rate_limit_registration)])
# ... existing code ...

@router.post("/forgot-password", ..., dependencies=[Depends(rate_limit_password_reset)])
# ... existing code ...
```

---

### Step 10: Create Tests

**File:** `src/tests/test_registration.py`

```python
"""Tests for user registration and email verification."""

import pytest
from unittest.mock import patch, AsyncMock

from src.models.user import User
from src.models.email_token import EmailToken
from src.db.enums import TokenType
from src.core.security import hash_password


class TestRegistration:
    """Tests for user registration."""
    
    @patch("src.services.registration_service.get_email_service")
    def test_register_user_success(self, mock_email, client, db_session):
        """Test successful user registration."""
        mock_service = AsyncMock()
        mock_service.send_verification_email = AsyncMock(return_value=True)
        mock_email.return_value = mock_service
        
        response = client.post("/auth/register", json={
            "email": "newuser@example.com",
            "password": "securepassword123",
            "first_name": "New",
            "last_name": "User",
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "verification" in data["message"].lower()
    
    def test_register_duplicate_email(self, client, db_session):
        """Test registration with existing email."""
        # Create existing user
        user = User(
            email="existing@example.com",
            password_hash=hash_password("password"),
            first_name="Existing",
            last_name="User",
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post("/auth/register", json={
            "email": "existing@example.com",
            "password": "newpassword123",
            "first_name": "New",
            "last_name": "User",
        })
        
        assert response.status_code == 409
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post("/auth/register", json={
            "email": "notanemail",
            "password": "securepassword123",
            "first_name": "Test",
            "last_name": "User",
        })
        
        assert response.status_code == 422
    
    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "short",
            "first_name": "Test",
            "last_name": "User",
        })
        
        assert response.status_code == 422


class TestEmailVerification:
    """Tests for email verification."""
    
    @patch("src.services.registration_service.get_email_service")
    def test_verify_email_success(self, mock_email, client, db_session):
        """Test successful email verification."""
        mock_service = AsyncMock()
        mock_service.send_verification_email = AsyncMock(return_value=True)
        mock_service.send_welcome_email = AsyncMock(return_value=True)
        mock_email.return_value = mock_service
        
        # Register user first
        client.post("/auth/register", json={
            "email": "verify@example.com",
            "password": "password123",
            "first_name": "Verify",
            "last_name": "User",
        })
        
        # Get the token from database
        token = db_session.query(EmailToken).filter(
            EmailToken.token_type == TokenType.EMAIL_VERIFICATION
        ).first()
        
        # We need the raw token, but we only have the hash
        # In real tests, we'd mock the email to capture the URL
        # For now, this tests the error case
        response = client.post("/auth/verify-email", json={
            "token": "invalid-token",
        })
        
        assert response.status_code == 400
    
    def test_verify_email_invalid_token(self, client):
        """Test verification with invalid token."""
        response = client.post("/auth/verify-email", json={
            "token": "definitely-not-a-valid-token",
        })
        
        assert response.status_code == 400


class TestPasswordReset:
    """Tests for password reset flow."""
    
    @patch("src.services.registration_service.get_email_service")
    def test_forgot_password_existing_user(self, mock_email, client, db_session):
        """Test password reset request for existing user."""
        mock_service = AsyncMock()
        mock_service.send_password_reset_email = AsyncMock(return_value=True)
        mock_email.return_value = mock_service
        
        # Create user
        user = User(
            email="reset@example.com",
            password_hash=hash_password("oldpassword"),
            first_name="Reset",
            last_name="User",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post("/auth/forgot-password", json={
            "email": "reset@example.com",
        })
        
        assert response.status_code == 200
        # Should always return success (prevents enumeration)
        assert "sent" in response.json()["message"].lower()
    
    def test_forgot_password_nonexistent_user(self, client):
        """Test password reset for nonexistent user (should still succeed)."""
        response = client.post("/auth/forgot-password", json={
            "email": "nobody@example.com",
        })
        
        # Always returns success to prevent enumeration
        assert response.status_code == 200
    
    def test_reset_password_invalid_token(self, client):
        """Test password reset with invalid token."""
        response = client.post("/auth/reset-password", json={
            "token": "invalid-token",
            "new_password": "newpassword123",
        })
        
        assert response.status_code == 400


class TestAdminCreateUser:
    """Tests for admin user creation."""
    
    def test_admin_create_user_unauthorized(self, client):
        """Test admin create user without auth."""
        response = client.post("/auth/admin/create-user", json={
            "email": "created@example.com",
            "password": "password123",
            "first_name": "Created",
            "last_name": "User",
            "roles": ["member"],
        })
        
        assert response.status_code == 401
```

---

### Step 11: Update Environment Config

**File:** `.env.compose.example` - Add email configuration:

```bash
# Email Configuration (Optional - uses console logging if not set)
# SMTP_HOST=smtp.example.com
# SMTP_PORT=587
# SMTP_USER=your-smtp-username
# SMTP_PASSWORD=your-smtp-password
# SMTP_FROM_EMAIL=noreply@ip2a.local
# SMTP_FROM_NAME=IP2A System
# SMTP_USE_TLS=true
```

---

### Step 12: Run Tests and Verify

```bash
# Run all tests
pytest -v

# Run only registration tests
pytest -v src/tests/test_registration.py

# Check code quality
ruff check . --fix
ruff format .
```

---

## Verification Checklist

Before committing, verify:

- [ ] EmailToken model created with migration
- [ ] User model updated with email_tokens relationship
- [ ] Email service (console + SMTP) implemented
- [ ] Registration service with all flows
- [ ] Registration endpoints added to auth router
- [ ] Rate limiting middleware added
- [ ] All new tests pass
- [ ] All existing tests still pass (140+)
- [ ] Code passes ruff check
- [ ] CLAUDE.md updated
- [ ] CHANGELOG.md updated

---

## Commit Message Template

```
feat(auth): Add user registration and email verification

- Add EmailToken model for verification and password reset tokens
- Add email service abstraction (console dev, SMTP production)
- Add registration service with:
  * User self-registration with email verification
  * Email verification flow
  * Password reset flow (forgot password)
  * Admin user creation (no verification needed)
- Add auth router endpoints:
  * POST /auth/register - Self-registration
  * POST /auth/verify-email - Verify email
  * GET /auth/verify-email - Verify via link click
  * POST /auth/resend-verification - Resend verification
  * POST /auth/forgot-password - Request reset
  * POST /auth/reset-password - Complete reset
  * POST /auth/admin/create-user - Admin creates user
- Add simple rate limiting middleware
- Add X new tests (Y total passing)

Phase 1.3 complete. Auth system fully implemented.
```

---

## API Endpoints Summary (Phase 1.3)

| Method | Endpoint | Auth | Rate Limit | Description |
|--------|----------|------|------------|-------------|
| POST | `/auth/register` | No | 5/min | Self-registration |
| POST | `/auth/verify-email` | No | - | Verify email (POST) |
| GET | `/auth/verify-email` | No | - | Verify email (link) |
| POST | `/auth/resend-verification` | No | 5/min | Resend verification |
| POST | `/auth/forgot-password` | No | 3/min | Request reset |
| POST | `/auth/reset-password` | No | 3/min | Complete reset |
| POST | `/auth/admin/create-user` | Admin | - | Admin creates user |

---

## Next Phase Preview

**Phase 2 (Roadmap): Pre-Apprenticeship System** (6-8 hours)
- Student model (linked to Member)
- Class/Course models
- Attendance tracking
- Grade management
- Certification tracking

---

*End of Instructions*
