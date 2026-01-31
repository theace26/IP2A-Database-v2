"""Tests for JWT utilities."""

import pytest
from datetime import timedelta

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
            additional_claims={"email": "test@example.com", "roles": ["admin"]},
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
            expires_delta=timedelta(seconds=-1),  # Already expired
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
