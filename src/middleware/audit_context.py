"""Audit context middleware for capturing request metadata."""

from typing import Optional
from contextvars import ContextVar
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Context variables for storing request metadata
_audit_user: ContextVar[Optional[str]] = ContextVar("audit_user", default=None)
_audit_ip: ContextVar[Optional[str]] = ContextVar("audit_ip", default=None)
_audit_user_agent: ContextVar[Optional[str]] = ContextVar("audit_user_agent", default=None)


class AuditContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to capture and store audit context from requests.

    This captures:
    - User ID (from auth headers or session)
    - IP address (from X-Forwarded-For or remote addr)
    - User-Agent string

    The context is stored in context vars and can be retrieved
    by audit logging functions.
    """

    async def dispatch(self, request: Request, call_next):
        """Process request and capture audit context."""

        # Extract user from auth header (if available)
        # For now, we'll use a simple approach. In production, this would
        # integrate with your auth system (JWT, session, etc.)
        user = _extract_user_from_request(request)
        _audit_user.set(user)

        # Get IP address (handle proxies)
        ip_address = _get_client_ip(request)
        _audit_ip.set(ip_address)

        # Get user agent
        user_agent = request.headers.get("user-agent")
        _audit_user_agent.set(user_agent)

        # Process request
        response = await call_next(request)

        # Clear context after request
        _audit_user.set(None)
        _audit_ip.set(None)
        _audit_user_agent.set(None)

        return response


def _extract_user_from_request(request: Request) -> str:
    """
    Extract user identifier from request.

    Priority:
    1. X-User-ID header (for authenticated requests)
    2. Authorization header (parse JWT/token)
    3. Session cookie
    4. "anonymous"

    Args:
        request: FastAPI request object

    Returns:
        User identifier string
    """
    # Check for user ID header (common in API gateways)
    if "x-user-id" in request.headers:
        return request.headers["x-user-id"]

    # Check for auth header
    if "authorization" in request.headers:
        # In a real system, you'd decode the JWT and extract user ID
        # For now, just return a placeholder
        auth_header = request.headers["authorization"]
        if auth_header.startswith("Bearer "):
            # TODO: Decode JWT and extract user ID
            return "authenticated_user"

    # Check for session cookie
    # if "session_id" in request.cookies:
    #     # TODO: Look up user from session
    #     pass

    return "anonymous"


def _get_client_ip(request: Request) -> Optional[str]:
    """
    Get client IP address, handling proxies and load balancers.

    Priority:
    1. X-Forwarded-For header (most common for proxies)
    2. X-Real-IP header
    3. request.client.host (direct connection)

    Args:
        request: FastAPI request object

    Returns:
        IP address string or None
    """
    # Check X-Forwarded-For (handles multiple proxies)
    if "x-forwarded-for" in request.headers:
        # Format: "client, proxy1, proxy2"
        # Take the first IP (original client)
        forwarded = request.headers["x-forwarded-for"]
        return forwarded.split(",")[0].strip()

    # Check X-Real-IP (single proxy)
    if "x-real-ip" in request.headers:
        return request.headers["x-real-ip"]

    # Direct connection
    if request.client:
        return request.client.host

    return None


def get_audit_context() -> dict:
    """
    Get current audit context for logging.

    Returns:
        Dictionary with changed_by, ip_address, user_agent
    """
    return {
        "changed_by": _audit_user.get(),
        "ip_address": _audit_ip.get(),
        "user_agent": _audit_user_agent.get(),
    }


def get_current_user() -> Optional[str]:
    """Get current user from audit context."""
    return _audit_user.get()


def get_current_ip() -> Optional[str]:
    """Get current IP address from audit context."""
    return _audit_ip.get()


def get_current_user_agent() -> Optional[str]:
    """Get current user agent from audit context."""
    return _audit_user_agent.get()
