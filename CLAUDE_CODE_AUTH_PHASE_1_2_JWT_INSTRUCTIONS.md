# Claude Code Instructions: Phase 1.2 - JWT Authentication

> **Project:** IP2A-Database-v2
> **Phase:** 1.2 - JWT Authentication Implementation
> **Estimated Time:** 4-6 hours
> **Prerequisites:** Phase 1.1 complete (User, Role, UserRole, RefreshToken models exist)

---

## Objective

Implement JWT-based authentication with:
- Password hashing (bcrypt)
- Access and refresh token generation/validation
- Login/logout endpoints
- Token refresh flow
- Role-based access control dependencies
- Protected route middleware

---

## Before You Start

### 1. Verify Environment

```bash
cd ~/Projects/IP2A-Database-v2
git status                    # Should be clean, on main
git pull origin main          # Get latest
pytest -v                     # Verify existing tests pass
```

### 2. Verify Phase 1.1 Models Exist

```bash
# These files should exist from Phase 1.1
ls src/models/user.py
ls src/models/role.py
ls src/models/user_role.py
ls src/models/refresh_token.py
ls src/db/enums/auth_enums.py
```

### 3. Read Key Files for Context

```bash
cat CLAUDE.md                          # Full project context
cat src/models/user.py                 # User model (has password_hash field)
cat src/models/refresh_token.py        # RefreshToken model
cat src/services/user_service.py       # Existing user service
```

---

## Implementation Steps

### Step 1: Add Dependencies

**File:** `requirements.txt` - Add these packages:

```
# Authentication
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
```

**Install in devcontainer:**

```bash
pip install passlib[bcrypt] python-jose[cryptography] --break-system-packages
```

---

### Step 2: Create Auth Configuration

**File:** `src/config/auth_config.py`

```python
"""Authentication configuration settings."""

import secrets
from datetime import timedelta
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    """Authentication settings loaded from environment variables."""
    
    # JWT Settings
    jwt_secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT signing. Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="Algorithm for JWT signing"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration in days"
    )
    
    # Password Settings
    password_min_length: int = Field(
        default=8,
        description="Minimum password length"
    )
    
    # Security Settings
    max_login_attempts: int = Field(
        default=5,
        description="Max failed login attempts before lockout"
    )
    lockout_duration_minutes: int = Field(
        default=30,
        description="Account lockout duration in minutes"
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
```

**Update `.env.compose.example`** - Add auth environment variables:

```bash
# Authentication (add to existing file)
AUTH_JWT_SECRET_KEY=your-secret-key-change-in-production
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=30
AUTH_REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

### Step 3: Create Password Utilities

**File:** `src/core/security.py`

```python
"""Security utilities for password hashing and verification."""

from passlib.context import CryptContext

# Password hashing context using bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Good balance of security and performance
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hash to verify against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)
```

---

### Step 4: Create JWT Utilities

**File:** `src/core/jwt.py`

```python
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
        to_encode,
        auth_settings.jwt_secret_key,
        algorithm=auth_settings.jwt_algorithm
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
            algorithms=[auth_settings.jwt_algorithm]
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
        options={"verify_signature": False}
    )
```

---

### Step 5: Create Core Module Init

**File:** `src/core/__init__.py`

```python
"""Core utilities and security functions."""

from src.core.security import hash_password, verify_password
from src.core.jwt import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    hash_refresh_token,
    TokenError,
    TokenExpiredError,
    TokenInvalidError,
)

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "verify_access_token",
    "hash_refresh_token",
    "TokenError",
    "TokenExpiredError",
    "TokenInvalidError",
]
```

---

### Step 6: Create Auth Schemas

**File:** `src/schemas/auth.py`

```python
"""Pydantic schemas for authentication."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema for login request."""
    
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Schema for token response after login."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""
    
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Schema for password change."""
    
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordResetRequest(BaseModel):
    """Schema for initiating password reset."""
    
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for confirming password reset with token."""
    
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class UserRegistrationRequest(BaseModel):
    """Schema for user registration."""
    
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


class CurrentUserResponse(BaseModel):
    """Schema for current user info (from /me endpoint)."""
    
    id: int
    email: str
    first_name: str
    last_name: str
    full_name: str
    is_active: bool
    is_verified: bool
    roles: list[str]
    last_login: Optional[datetime] = None
    member_id: Optional[int] = None
```

**Update `src/schemas/__init__.py`** - Add auth schema exports:

```python
# Auth schemas
from src.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserRegistrationRequest,
    CurrentUserResponse,
)

# Add to __all__
__all__ = [
    # ... existing exports ...
    # Auth
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "UserRegistrationRequest",
    "CurrentUserResponse",
]
```

---

### Step 7: Create Auth Service

**File:** `src/services/auth_service.py`

```python
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
        }
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
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()
    
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
    
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()
    
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
    
    result = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False
    ).update({
        "is_revoked": True,
        "revoked_at": now
    })
    
    db.commit()
    return result


def change_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str
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
    
    result = db.query(RefreshToken).filter(
        RefreshToken.expires_at < now
    ).delete()
    
    db.commit()
    return result
```

---

### Step 8: Create Auth Dependencies

**File:** `src/routers/dependencies/auth.py`

```python
"""Authentication dependencies for FastAPI routes."""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models.user import User
from src.core.jwt import verify_access_token, TokenExpiredError, TokenInvalidError
from src.services.user_service import get_user


# HTTP Bearer scheme for token extraction
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(security)
    ],
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Usage:
        @router.get("/protected")
        def protected_route(user: User = Depends(get_current_user)):
            return {"user": user.email}
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = verify_access_token(credentials.credentials)
        user_id = int(payload.get("sub"))
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    return user


async def get_current_user_optional(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(security)
    ],
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Dependency to optionally get the current user.
    
    Returns None if not authenticated (doesn't raise error).
    
    Usage:
        @router.get("/public-or-private")
        def route(user: Optional[User] = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello {user.first_name}"}
            return {"message": "Hello guest"}
    """
    if not credentials:
        return None
    
    try:
        payload = verify_access_token(credentials.credentials)
        user_id = int(payload.get("sub"))
        user = get_user(db, user_id)
        if user and user.is_active:
            return user
    except (TokenExpiredError, TokenInvalidError, ValueError, TypeError):
        pass
    
    return None


def require_roles(*required_roles: str):
    """
    Dependency factory to require specific roles.
    
    Usage:
        @router.get("/admin-only")
        def admin_route(user: User = Depends(require_roles("admin"))):
            return {"message": "Admin access granted"}
        
        @router.get("/officer-or-admin")
        def officer_route(user: User = Depends(require_roles("admin", "officer"))):
            return {"message": "Access granted"}
    """
    async def role_checker(
        user: User = Depends(get_current_user),
    ) -> User:
        user_roles = {r.lower() for r in user.role_names}
        required = {r.lower() for r in required_roles}
        
        if not user_roles.intersection(required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role(s): {', '.join(required_roles)}",
            )
        
        return user
    
    return role_checker


def require_verified_email():
    """
    Dependency to require a verified email address.
    
    Usage:
        @router.get("/verified-only")
        def verified_route(user: User = Depends(require_verified_email())):
            return {"message": "Email verified"}
    """
    async def verified_checker(
        user: User = Depends(get_current_user),
    ) -> User:
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required",
            )
        return user
    
    return verified_checker


# Type aliases for cleaner route signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[Optional[User], Depends(get_current_user_optional)]
AdminUser = Annotated[User, Depends(require_roles("admin"))]
OfficerUser = Annotated[User, Depends(require_roles("admin", "officer"))]
StaffUser = Annotated[User, Depends(require_roles("admin", "officer", "staff"))]
```

**Create dependencies __init__.py:**

**File:** `src/routers/dependencies/__init__.py`

```python
"""FastAPI dependencies."""

from src.routers.dependencies.auth import (
    get_current_user,
    get_current_user_optional,
    require_roles,
    require_verified_email,
    CurrentUser,
    OptionalUser,
    AdminUser,
    OfficerUser,
    StaffUser,
)

__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "require_roles",
    "require_verified_email",
    "CurrentUser",
    "OptionalUser",
    "AdminUser",
    "OfficerUser",
    "StaffUser",
]
```

---

### Step 9: Create Auth Router

**File:** `src/routers/auth.py`

```python
"""Authentication router for login, logout, and token management."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordChangeRequest,
    CurrentUserResponse,
)
from src.services.auth_service import (
    authenticate_user,
    create_tokens,
    refresh_access_token,
    revoke_refresh_token,
    revoke_all_user_tokens,
    change_password,
    InvalidCredentialsError,
    AccountLockedError,
    AccountInactiveError,
    TokenRevokedError,
)
from src.routers.dependencies.auth import get_current_user, CurrentUser


router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract device info and IP from request."""
    # Get user agent
    device_info = request.headers.get("user-agent", "")[:500]  # Limit length
    
    # Get real IP (handle proxies)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else None
    
    return device_info, ip_address


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and return tokens.
    
    Returns access token (short-lived) and refresh token (long-lived).
    Store refresh token securely (httpOnly cookie or secure storage).
    """
    try:
        user = authenticate_user(db, login_data.email, login_data.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=str(e),
        )
    except AccountInactiveError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    
    device_info, ip_address = get_client_info(request)
    tokens = create_tokens(db, user, device_info, ip_address)
    
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    
    Implements token rotation: old refresh token is revoked,
    new refresh token is issued.
    """
    try:
        device_info, ip_address = get_client_info(request)
        tokens = refresh_access_token(
            db,
            refresh_data.refresh_token,
            device_info,
            ip_address,
        )
        return TokenResponse(**tokens)
    except TokenRevokedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Logout from current device by revoking the refresh token.
    
    Client should also discard the access token.
    """
    revoke_refresh_token(db, refresh_data.refresh_token)
    return None


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all_devices(
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Logout from all devices by revoking all refresh tokens.
    
    Requires valid access token.
    """
    revoke_all_user_tokens(db, user.id)
    return None


@router.get("/me", response_model=CurrentUserResponse)
def get_current_user_info(user: CurrentUser):
    """
    Get current authenticated user's information.
    """
    return CurrentUserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        roles=user.role_names,
        last_login=user.last_login,
        member_id=user.member_id,
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_user_password(
    password_data: PasswordChangeRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Change the current user's password.
    
    After changing, all existing sessions are invalidated.
    """
    try:
        change_password(
            db,
            user,
            password_data.current_password,
            password_data.new_password,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    return None
```

---

### Step 10: Register Auth Router

**File:** `src/routers/__init__.py` - Add auth router:

```python
# Add to existing imports
from src.routers.auth import router as auth_router

# Add to router list for registration
__all__ = [
    # ... existing routers ...
    "auth_router",
]
```

**File:** `src/main.py` - Include auth router:

```python
# Add to router includes
from src.routers.auth import router as auth_router

# In app setup section
app.include_router(auth_router)
```

---

### Step 11: Update User Service for Registration

**File:** `src/services/user_service.py` - Update create_user to use hashing:

```python
# Add import at top
from src.core.security import hash_password

# Update create_user function
def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Create a new user with hashed password.
    
    Note: If password_hash is provided directly (for internal use),
    use the existing pattern. For user registration, password is hashed here.
    """
    user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        password_hash=hash_password(user_data.password),
        member_id=user_data.member_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

---

### Step 12: Create Auth Tests

**File:** `src/tests/test_auth_jwt.py`

```python
"""Tests for JWT utilities."""

import pytest
from datetime import timedelta
from time import sleep

from src.core.jwt import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    hash_refresh_token,
    TokenExpiredError,
    TokenInvalidError,
)


class TestAccessToken:
    """Tests for access token creation and verification."""
    
    def test_create_access_token(self):
        """Test creating an access token."""
        token = create_access_token(subject=123)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_verify_access_token(self):
        """Test verifying a valid access token."""
        token = create_access_token(
            subject=456,
            additional_claims={"email": "test@example.com", "roles": ["admin"]}
        )
        
        payload = verify_access_token(token)
        
        assert payload["sub"] == "456"
        assert payload["email"] == "test@example.com"
        assert payload["roles"] == ["admin"]
        assert payload["type"] == "access"
    
    def test_access_token_expired(self):
        """Test that expired tokens raise error."""
        token = create_access_token(
            subject=789,
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        with pytest.raises(TokenExpiredError):
            verify_access_token(token)
    
    def test_invalid_token(self):
        """Test that invalid tokens raise error."""
        with pytest.raises(TokenInvalidError):
            verify_access_token("not.a.valid.token")
    
    def test_tampered_token(self):
        """Test that tampered tokens raise error."""
        token = create_access_token(subject=123)
        # Tamper with the token
        tampered = token[:-5] + "xxxxx"
        
        with pytest.raises(TokenInvalidError):
            verify_access_token(tampered)


class TestRefreshToken:
    """Tests for refresh token creation."""
    
    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        raw_token, token_hash, expires_at = create_refresh_token(subject=123)
        
        assert raw_token is not None
        assert len(raw_token) > 20
        assert token_hash is not None
        assert len(token_hash) == 64  # SHA-256 hex
        assert expires_at is not None
    
    def test_hash_refresh_token(self):
        """Test that hashing is consistent."""
        raw_token, original_hash, _ = create_refresh_token(subject=123)
        
        # Hashing the raw token should produce same hash
        computed_hash = hash_refresh_token(raw_token)
        assert computed_hash == original_hash
    
    def test_refresh_tokens_unique(self):
        """Test that each refresh token is unique."""
        token1, hash1, _ = create_refresh_token(subject=123)
        token2, hash2, _ = create_refresh_token(subject=123)
        
        assert token1 != token2
        assert hash1 != hash2
```

**File:** `src/tests/test_auth_service.py`

```python
"""Tests for authentication service."""

import pytest
from datetime import datetime, timedelta, timezone

from src.models.user import User
from src.models.refresh_token import RefreshToken
from src.core.security import hash_password
from src.services.auth_service import (
    authenticate_user,
    create_tokens,
    refresh_access_token,
    revoke_refresh_token,
    revoke_all_user_tokens,
    change_password,
    InvalidCredentialsError,
    AccountLockedError,
    AccountInactiveError,
    TokenRevokedError,
)


class TestAuthentication:
    """Tests for user authentication."""
    
    def test_authenticate_valid_credentials(self, db_session):
        """Test successful authentication."""
        user = User(
            email="auth@example.com",
            password_hash=hash_password("correctpassword"),
            first_name="Auth",
            last_name="Test",
        )
        db_session.add(user)
        db_session.commit()
        
        authenticated = authenticate_user(
            db_session, "auth@example.com", "correctpassword"
        )
        
        assert authenticated.id == user.id
        assert authenticated.last_login is not None
    
    def test_authenticate_wrong_password(self, db_session):
        """Test authentication with wrong password."""
        user = User(
            email="wrongpw@example.com",
            password_hash=hash_password("correctpassword"),
            first_name="Wrong",
            last_name="Password",
        )
        db_session.add(user)
        db_session.commit()
        
        with pytest.raises(InvalidCredentialsError):
            authenticate_user(db_session, "wrongpw@example.com", "wrongpassword")
    
    def test_authenticate_nonexistent_user(self, db_session):
        """Test authentication with nonexistent email."""
        with pytest.raises(InvalidCredentialsError):
            authenticate_user(db_session, "nobody@example.com", "password")
    
    def test_authenticate_inactive_user(self, db_session):
        """Test authentication fails for inactive user."""
        user = User(
            email="inactive@example.com",
            password_hash=hash_password("password"),
            first_name="Inactive",
            last_name="User",
            is_active=False,
        )
        db_session.add(user)
        db_session.commit()
        
        with pytest.raises(AccountInactiveError):
            authenticate_user(db_session, "inactive@example.com", "password")
    
    def test_authenticate_locked_account(self, db_session):
        """Test authentication fails for locked account."""
        user = User(
            email="locked@example.com",
            password_hash=hash_password("password"),
            first_name="Locked",
            last_name="User",
            locked_until=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(user)
        db_session.commit()
        
        with pytest.raises(AccountLockedError):
            authenticate_user(db_session, "locked@example.com", "password")


class TestTokenOperations:
    """Tests for token creation and refresh."""
    
    def test_create_tokens(self, db_session):
        """Test token creation."""
        user = User(
            email="tokens@example.com",
            password_hash=hash_password("password"),
            first_name="Token",
            last_name="Test",
        )
        db_session.add(user)
        db_session.commit()
        
        tokens = create_tokens(db_session, user)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert tokens["expires_in"] > 0
        
        # Verify refresh token stored in DB
        db_token = db_session.query(RefreshToken).filter(
            RefreshToken.user_id == user.id
        ).first()
        assert db_token is not None
    
    def test_refresh_access_token(self, db_session):
        """Test refreshing access token."""
        user = User(
            email="refresh@example.com",
            password_hash=hash_password("password"),
            first_name="Refresh",
            last_name="Test",
        )
        db_session.add(user)
        db_session.commit()
        
        # Create initial tokens
        initial_tokens = create_tokens(db_session, user)
        
        # Refresh
        new_tokens = refresh_access_token(
            db_session, initial_tokens["refresh_token"]
        )
        
        assert new_tokens["access_token"] != initial_tokens["access_token"]
        assert new_tokens["refresh_token"] != initial_tokens["refresh_token"]
    
    def test_refresh_revoked_token(self, db_session):
        """Test refreshing a revoked token fails."""
        user = User(
            email="revoked@example.com",
            password_hash=hash_password("password"),
            first_name="Revoked",
            last_name="Test",
        )
        db_session.add(user)
        db_session.commit()
        
        tokens = create_tokens(db_session, user)
        revoke_refresh_token(db_session, tokens["refresh_token"])
        
        with pytest.raises(TokenRevokedError):
            refresh_access_token(db_session, tokens["refresh_token"])
    
    def test_revoke_all_tokens(self, db_session):
        """Test revoking all user tokens."""
        user = User(
            email="revokeall@example.com",
            password_hash=hash_password("password"),
            first_name="Revoke",
            last_name="All",
        )
        db_session.add(user)
        db_session.commit()
        
        # Create multiple tokens (different devices)
        tokens1 = create_tokens(db_session, user, device_info="Device 1")
        tokens2 = create_tokens(db_session, user, device_info="Device 2")
        
        # Revoke all
        count = revoke_all_user_tokens(db_session, user.id)
        assert count == 2
        
        # Both should now fail
        with pytest.raises(TokenRevokedError):
            refresh_access_token(db_session, tokens1["refresh_token"])
        
        with pytest.raises(TokenRevokedError):
            refresh_access_token(db_session, tokens2["refresh_token"])


class TestPasswordChange:
    """Tests for password change."""
    
    def test_change_password_success(self, db_session):
        """Test successful password change."""
        user = User(
            email="changepw@example.com",
            password_hash=hash_password("oldpassword"),
            first_name="Change",
            last_name="Password",
        )
        db_session.add(user)
        db_session.commit()
        
        result = change_password(
            db_session, user, "oldpassword", "newpassword123"
        )
        
        assert result is True
        
        # Old password should fail
        with pytest.raises(InvalidCredentialsError):
            authenticate_user(db_session, "changepw@example.com", "oldpassword")
        
        # New password should work
        authenticated = authenticate_user(
            db_session, "changepw@example.com", "newpassword123"
        )
        assert authenticated.id == user.id
    
    def test_change_password_wrong_current(self, db_session):
        """Test password change with wrong current password."""
        user = User(
            email="wrongcurrent@example.com",
            password_hash=hash_password("correctpassword"),
            first_name="Wrong",
            last_name="Current",
        )
        db_session.add(user)
        db_session.commit()
        
        with pytest.raises(InvalidCredentialsError):
            change_password(
                db_session, user, "wrongpassword", "newpassword123"
            )
```

**File:** `src/tests/test_auth_router.py`

```python
"""Tests for authentication router endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.models.user import User
from src.core.security import hash_password


class TestLoginEndpoint:
    """Tests for /auth/login endpoint."""
    
    def test_login_success(self, client: TestClient, db_session):
        """Test successful login."""
        user = User(
            email="login@example.com",
            password_hash=hash_password("password123"),
            first_name="Login",
            last_name="Test",
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post("/auth/login", json={
            "email": "login@example.com",
            "password": "password123",
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client: TestClient, db_session):
        """Test login with wrong password."""
        user = User(
            email="wrongpw@example.com",
            password_hash=hash_password("correctpassword"),
            first_name="Wrong",
            last_name="PW",
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post("/auth/login", json={
            "email": "wrongpw@example.com",
            "password": "wrongpassword",
        })
        
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with nonexistent email."""
        response = client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "password",
        })
        
        assert response.status_code == 401


class TestMeEndpoint:
    """Tests for /auth/me endpoint."""
    
    def test_me_authenticated(self, client: TestClient, db_session):
        """Test getting current user info."""
        user = User(
            email="me@example.com",
            password_hash=hash_password("password123"),
            first_name="Current",
            last_name="User",
        )
        db_session.add(user)
        db_session.commit()
        
        # Login first
        login_response = client.post("/auth/login", json={
            "email": "me@example.com",
            "password": "password123",
        })
        access_token = login_response.json()["access_token"]
        
        # Get /me
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["first_name"] == "Current"
        assert data["last_name"] == "User"
    
    def test_me_unauthenticated(self, client: TestClient):
        """Test /me without token."""
        response = client.get("/auth/me")
        assert response.status_code == 401


class TestRefreshEndpoint:
    """Tests for /auth/refresh endpoint."""
    
    def test_refresh_success(self, client: TestClient, db_session):
        """Test token refresh."""
        user = User(
            email="refresh@example.com",
            password_hash=hash_password("password123"),
            first_name="Refresh",
            last_name="Test",
        )
        db_session.add(user)
        db_session.commit()
        
        # Login
        login_response = client.post("/auth/login", json={
            "email": "refresh@example.com",
            "password": "password123",
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh
        response = client.post("/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


class TestLogoutEndpoint:
    """Tests for /auth/logout endpoint."""
    
    def test_logout_success(self, client: TestClient, db_session):
        """Test logout."""
        user = User(
            email="logout@example.com",
            password_hash=hash_password("password123"),
            first_name="Logout",
            last_name="Test",
        )
        db_session.add(user)
        db_session.commit()
        
        # Login
        login_response = client.post("/auth/login", json={
            "email": "logout@example.com",
            "password": "password123",
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Logout
        response = client.post("/auth/logout", json={
            "refresh_token": refresh_token,
        })
        
        assert response.status_code == 204
        
        # Refresh should fail now
        refresh_response = client.post("/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert refresh_response.status_code == 401
```

---

### Step 13: Run Tests and Verify

```bash
# Run all tests
pytest -v

# Run only auth tests
pytest -v src/tests/test_auth_jwt.py src/tests/test_auth_service.py src/tests/test_auth_router.py

# Check code quality
ruff check . --fix
ruff format .
```

---

### Step 14: Update Documentation

**Update CLAUDE.md** - Add auth section:

```markdown
### Authentication (Phase 1.2)
- JWT-based authentication with access + refresh tokens
- Password hashing with bcrypt (12 rounds)
- Token rotation on refresh
- Account lockout after 5 failed attempts (30 min)
- Dependencies: `get_current_user`, `require_roles()`, `CurrentUser`
```

**Update CHANGELOG.md**:

```markdown
## [Unreleased]

### Added
- JWT authentication system (Phase 1.2)
  * Access tokens (30 min) and refresh tokens (7 days)
  * Password hashing with bcrypt
  * Token rotation on refresh
  * Account lockout after failed attempts
  * Auth endpoints: login, logout, refresh, me, change-password
  * Role-based access control dependencies
```

---

## Verification Checklist

Before committing, verify:

- [ ] Dependencies installed (passlib, python-jose)
- [ ] Auth config created with env variables
- [ ] Password hashing utilities working
- [ ] JWT creation and verification working
- [ ] Auth service with all operations
- [ ] Auth dependencies for protected routes
- [ ] Auth router with all endpoints
- [ ] Router registered in main.py
- [ ] All new tests pass
- [ ] All existing tests still pass
- [ ] Code passes ruff check
- [ ] CLAUDE.md updated
- [ ] CHANGELOG.md updated

---

## Commit Message Template

```
feat(auth): Implement JWT authentication system

- Add passlib/bcrypt for password hashing
- Add python-jose for JWT token handling
- Add auth config with environment variables
- Add core security utilities (hash, verify password)
- Add core JWT utilities (create, verify tokens)
- Add auth service (login, logout, refresh, change password)
- Add auth dependencies (get_current_user, require_roles)
- Add auth router with endpoints:
  * POST /auth/login - Get access + refresh tokens
  * POST /auth/refresh - Refresh access token
  * POST /auth/logout - Revoke refresh token
  * POST /auth/logout-all - Revoke all user tokens
  * GET /auth/me - Get current user info
  * POST /auth/change-password - Change password
- Add comprehensive tests (X new tests passing)

Phase 1.2 complete. Ready for Phase 1.3 (User registration + email verification).
```

---

## API Endpoints Summary

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/auth/login` | No | Login, get tokens |
| POST | `/auth/refresh` | No | Refresh access token |
| POST | `/auth/logout` | No | Logout (revoke refresh token) |
| POST | `/auth/logout-all` | Yes | Logout all devices |
| GET | `/auth/me` | Yes | Get current user info |
| POST | `/auth/change-password` | Yes | Change password |

---

## Next Phase Preview

**Phase 1.3: User Registration & Email Verification** (3-4 hours)
- User registration endpoint
- Email verification token generation
- Email service integration (SMTP or provider)
- Password reset flow
- Rate limiting on auth endpoints

---

*End of Instructions*
