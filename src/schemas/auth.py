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


class UserRegistrationResponse(BaseModel):
    """Schema for registration response."""

    id: int
    email: str
    first_name: str
    last_name: str
    message: str = (
        "Registration successful. Please check your email to verify your account."
    )


class EmailVerificationRequest(BaseModel):
    """Schema for email verification."""

    token: str


class ResendVerificationRequest(BaseModel):
    """Schema for resending verification email."""

    email: EmailStr


class AdminUserCreateRequest(BaseModel):
    """Schema for admin creating a user."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    roles: list[str] = Field(default=["member"])
    is_verified: bool = True
    member_id: Optional[int] = None


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
