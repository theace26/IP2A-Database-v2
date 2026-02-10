"""
Cookie-based authentication for frontend routes.
Uses HTTP-only cookies to store JWT tokens securely.
"""

from typing import Optional
import logging

from fastapi import Cookie, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from src.core.jwt import (
    verify_access_token,
    TokenExpiredError,
    TokenInvalidError,
)
from src.db.session import get_db

logger = logging.getLogger(__name__)


class AuthenticationRequired:
    """
    Dependency that requires a valid JWT cookie.
    Redirects to login page if not authenticated.
    """

    def __init__(self, redirect_to_login: bool = True):
        self.redirect_to_login = redirect_to_login

    async def __call__(
        self,
        request: Request,
        access_token: Optional[str] = Cookie(default=None),
    ):
        """
        Validate the access_token cookie.

        Returns:
            User dict if valid token

        Raises:
            RedirectResponse to /login if redirect_to_login=True
            HTTPException 401 if redirect_to_login=False
        """
        if not access_token:
            return self._handle_unauthorized(request)

        try:
            # Verify the JWT token
            payload = verify_access_token(access_token)
            if not payload:
                return self._handle_unauthorized(request)

            user_id = payload.get("sub")
            if not user_id:
                return self._handle_unauthorized(request)

            # Check if user must change password
            must_change_password = payload.get("must_change_password", False)
            current_path = str(request.url.path)

            # Redirect to change password if required (except for change-password and logout)
            if must_change_password and current_path not in [
                "/auth/change-password",
                "/logout",
            ]:
                return RedirectResponse(
                    url="/auth/change-password",
                    status_code=status.HTTP_302_FOUND,
                )

            # Get viewing_as from session if user is developer
            viewing_as = None
            roles = payload.get("roles", [])
            if "developer" in roles and hasattr(request, "session"):
                viewing_as = request.session.get("viewing_as")

            # Return user info from token (avoid DB call on every request)
            return {
                "id": int(user_id),
                "email": payload.get("email"),
                "roles": roles,
                "must_change_password": must_change_password,
                "viewing_as": viewing_as,  # None for non-developers or when not impersonating
            }

        except TokenExpiredError:
            logger.debug("Access token expired")
            return self._handle_unauthorized(request)
        except TokenInvalidError as e:
            logger.warning(f"Token validation failed: {e}")
            return self._handle_unauthorized(request)
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")
            return self._handle_unauthorized(request)

    def _handle_unauthorized(self, request: Request):
        """Handle unauthorized access by clearing invalid cookies and redirecting."""
        if self.redirect_to_login:
            # Store the original URL to redirect back after login
            return_url = str(request.url.path)
            response = RedirectResponse(
                url=f"/login?next={return_url}&message=Please+log+in+to+continue&type=info",
                status_code=status.HTTP_302_FOUND,
            )
            # Clear any invalid cookies to prevent repeated validation errors
            response.delete_cookie("access_token", path="/")
            response.delete_cookie("refresh_token", path="/")
            return response
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )


# Convenience instances
require_auth = AuthenticationRequired(redirect_to_login=True)
require_auth_api = AuthenticationRequired(redirect_to_login=False)


async def get_current_user_from_cookie(
    request: Request,
    access_token: Optional[str] = Cookie(default=None),
) -> Optional[dict]:
    """
    Get current user from cookie without raising exceptions.
    Returns None if not authenticated.
    Useful for pages that work both with and without auth.
    """
    if not access_token:
        return None

    try:
        payload = verify_access_token(access_token)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        # Get viewing_as from session if user is developer
        viewing_as = None
        roles = payload.get("roles", [])
        if "developer" in roles and hasattr(request, "session"):
            viewing_as = request.session.get("viewing_as")

        return {
            "id": int(user_id),
            "email": payload.get("email"),
            "roles": roles,
            "viewing_as": viewing_as,
        }
    except (TokenExpiredError, TokenInvalidError):
        return None
    except Exception:
        return None


async def get_current_user_model(
    request: Request,
    access_token: Optional[str] = Cookie(default=None),
    db=None,
):
    """
    Get the full User model from database using cookie authentication.
    Returns User model instance or raises RedirectResponse/HTTPException.

    Usage:
        @router.get("/page")
        async def page(
            current_user: User = Depends(get_current_user_model),
            db: Session = Depends(get_db),
        ):
            ...
    """
    from src.models.user import User

    # First verify the cookie
    if not access_token:
        response = RedirectResponse(
            url=f"/login?next={request.url.path}",
            status_code=status.HTTP_302_FOUND,
        )
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")
        return response

    try:
        payload = verify_access_token(access_token)
        if not payload:
            raise TokenInvalidError("Invalid token")

        user_id = int(payload.get("sub"))

        # Get database session if not provided
        if db is None:
            db = next(get_db())

        # Fetch actual User model from database
        user = db.query(User).filter(User.id == user_id).first()

        if not user or not user.is_active:
            response = RedirectResponse(
                url="/login?message=User+not+found+or+inactive",
                status_code=status.HTTP_302_FOUND,
            )
            response.delete_cookie("access_token", path="/")
            response.delete_cookie("refresh_token", path="/")
            return response

        return user

    except (TokenExpiredError, TokenInvalidError):
        response = RedirectResponse(
            url=f"/login?next={request.url.path}",
            status_code=status.HTTP_302_FOUND,
        )
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")
        return response
    except Exception as e:
        logger.error(f"Error fetching user model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching user information",
        )
