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
    UserRegistrationRequest,
    UserRegistrationResponse,
    EmailVerificationRequest,
    ResendVerificationRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    AdminUserCreateRequest,
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
from src.routers.dependencies.auth import CurrentUser, AdminUser
from src.middleware.rate_limit import (
    rate_limit_auth,
    rate_limit_registration,
    rate_limit_password_reset,
)


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


@router.post(
    "/login", response_model=TokenResponse, dependencies=[Depends(rate_limit_auth)]
)
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


@router.post(
    "/register",
    response_model=UserRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_registration)],
)
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
    return {
        "message": "If the email exists and is unverified, a verification email has been sent."
    }


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit_password_reset)],
)
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


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit_password_reset)],
)
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


@router.post(
    "/admin/create-user",
    response_model=UserRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
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
