"""Authentication dependencies for FastAPI routes."""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models.user import User
from src.core.jwt import verify_access_token, TokenExpiredError, TokenInvalidError
from src.services.user_service import get_user


# HTTP Bearer scheme for token extraction
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
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
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
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
