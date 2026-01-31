"""Simple in-memory rate limiting middleware."""

import time
from collections import defaultdict
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
