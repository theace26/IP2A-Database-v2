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
from src.routers.dependencies.auth import CurrentUser


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
