"""Tests for rate limiting middleware."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request

from src.middleware.rate_limit import (
    RateLimiter,
    auth_rate_limiter,
    registration_rate_limiter,
    password_reset_rate_limiter,
    rate_limit_auth,
    rate_limit_registration,
    rate_limit_password_reset,
)


class TestRateLimiter:
    """Test the RateLimiter class."""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initializes with correct settings."""
        limiter = RateLimiter(requests_per_minute=5)
        assert limiter.requests_per_minute == 5
        assert isinstance(limiter.requests, dict)

    def test_rate_limiter_allows_first_request(self):
        """Test first request is not rate limited."""
        limiter = RateLimiter(requests_per_minute=5)
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        assert limiter.is_rate_limited(request) is False

    def test_rate_limiter_allows_under_limit(self):
        """Test requests under limit are allowed."""
        limiter = RateLimiter(requests_per_minute=5)
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        # Make 4 requests (under limit of 5)
        for _ in range(4):
            assert limiter.is_rate_limited(request) is False

    def test_rate_limiter_blocks_over_limit(self):
        """Test requests over limit are blocked."""
        limiter = RateLimiter(requests_per_minute=5)
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        # Make 5 requests (at limit)
        for _ in range(5):
            limiter.is_rate_limited(request)

        # 6th request should be blocked
        assert limiter.is_rate_limited(request) is True

    def test_rate_limiter_uses_forwarded_header(self):
        """Test rate limiter uses X-Forwarded-For header."""
        limiter = RateLimiter(requests_per_minute=5)
        request = MagicMock(spec=Request)
        request.headers = {"x-forwarded-for": "1.2.3.4, 5.6.7.8"}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        limiter.is_rate_limited(request)
        # Check the client ID was extracted from forwarded header
        assert "1.2.3.4" in limiter.requests

    def test_rate_limiter_separates_clients(self):
        """Test rate limiter tracks clients separately."""
        limiter = RateLimiter(requests_per_minute=2)

        request1 = MagicMock(spec=Request)
        request1.headers = {}
        request1.client = MagicMock()
        request1.client.host = "10.0.0.1"

        request2 = MagicMock(spec=Request)
        request2.headers = {}
        request2.client = MagicMock()
        request2.client.host = "10.0.0.2"

        # Client 1 makes 2 requests (at limit)
        limiter.is_rate_limited(request1)
        limiter.is_rate_limited(request1)

        # Client 2 should still be allowed
        assert limiter.is_rate_limited(request2) is False

    def test_rate_limiter_raises_exception(self):
        """Test rate limiter raises HTTPException when exceeded."""
        from fastapi import HTTPException

        limiter = RateLimiter(requests_per_minute=1)
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        # First request succeeds
        limiter(request)

        # Second request should raise
        with pytest.raises(HTTPException) as exc_info:
            limiter(request)

        assert exc_info.value.status_code == 429
        assert "Too many requests" in exc_info.value.detail


class TestPredefinedRateLimiters:
    """Test predefined rate limiters."""

    def test_auth_rate_limiter_exists(self):
        """Test auth rate limiter is configured."""
        assert auth_rate_limiter.requests_per_minute == 10

    def test_registration_rate_limiter_exists(self):
        """Test registration rate limiter is configured."""
        assert registration_rate_limiter.requests_per_minute == 5

    def test_password_reset_rate_limiter_exists(self):
        """Test password reset rate limiter is configured."""
        assert password_reset_rate_limiter.requests_per_minute == 3


class TestRateLimitFunctions:
    """Test rate limit dependency functions."""

    def test_rate_limit_auth_function(self):
        """Test rate_limit_auth function."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        # Should not raise on first call
        rate_limit_auth(request)

    def test_rate_limit_registration_function(self):
        """Test rate_limit_registration function."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.2"

        # Should not raise on first call
        rate_limit_registration(request)

    def test_rate_limit_password_reset_function(self):
        """Test rate_limit_password_reset function."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.3"

        # Should not raise on first call
        rate_limit_password_reset(request)
