"""Tests for authentication service."""

import pytest
import uuid
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
        email = f"auth_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash=hash_password("correctpassword"),
            first_name="Auth",
            last_name="Test",
        )
        db_session.add(user)
        db_session.commit()

        authenticated = authenticate_user(db_session, email, "correctpassword")

        assert authenticated.id == user.id
        assert authenticated.last_login is not None

    def test_authenticate_wrong_password(self, db_session):
        """Test authentication with wrong password."""
        email = f"wrongpw_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash=hash_password("correctpassword"),
            first_name="Wrong",
            last_name="Password",
        )
        db_session.add(user)
        db_session.commit()

        with pytest.raises(InvalidCredentialsError):
            authenticate_user(db_session, email, "wrongpassword")

    def test_authenticate_nonexistent_user(self, db_session):
        """Test authentication with nonexistent email."""
        with pytest.raises(InvalidCredentialsError):
            authenticate_user(db_session, "nobody@example.com", "password")

    def test_authenticate_inactive_user(self, db_session):
        """Test authentication fails for inactive user."""
        email = f"inactive_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash=hash_password("password"),
            first_name="Inactive",
            last_name="User",
            is_active=False,
        )
        db_session.add(user)
        db_session.commit()

        with pytest.raises(AccountInactiveError):
            authenticate_user(db_session, email, "password")

    def test_authenticate_locked_account(self, db_session):
        """Test authentication fails for locked account."""
        email = f"locked_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash=hash_password("password"),
            first_name="Locked",
            last_name="User",
            locked_until=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(user)
        db_session.commit()

        with pytest.raises(AccountLockedError):
            authenticate_user(db_session, email, "password")


class TestTokenOperations:
    """Tests for token creation and refresh."""

    def test_create_tokens(self, db_session):
        """Test token creation."""
        email = f"tokens_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
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
        db_token = (
            db_session.query(RefreshToken)
            .filter(RefreshToken.user_id == user.id)
            .first()
        )
        assert db_token is not None

    def test_refresh_access_token(self, db_session):
        """Test refreshing access token."""
        email = f"refresh_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash=hash_password("password"),
            first_name="Refresh",
            last_name="Test",
        )
        db_session.add(user)
        db_session.commit()

        # Create initial tokens
        initial_tokens = create_tokens(db_session, user)

        # Refresh
        new_tokens = refresh_access_token(db_session, initial_tokens["refresh_token"])

        # Both should be valid tokens
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert len(new_tokens["access_token"]) > 50
        assert len(new_tokens["refresh_token"]) > 20
        # Refresh tokens should always be different (token rotation)
        assert new_tokens["refresh_token"] != initial_tokens["refresh_token"]

    def test_refresh_revoked_token(self, db_session):
        """Test refreshing a revoked token fails."""
        email = f"revoked_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
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
        email = f"revokeall_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
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
        email = f"changepw_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash=hash_password("oldpassword"),
            first_name="Change",
            last_name="Password",
        )
        db_session.add(user)
        db_session.commit()

        result = change_password(db_session, user, "oldpassword", "newpassword123")

        assert result is True

        # Old password should fail
        with pytest.raises(InvalidCredentialsError):
            authenticate_user(db_session, email, "oldpassword")

        # New password should work
        authenticated = authenticate_user(db_session, email, "newpassword123")
        assert authenticated.id == user.id

    def test_change_password_wrong_current(self, db_session):
        """Test password change with wrong current password."""
        email = f"wrongcurrent_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash=hash_password("correctpassword"),
            first_name="Wrong",
            last_name="Current",
        )
        db_session.add(user)
        db_session.commit()

        with pytest.raises(InvalidCredentialsError):
            change_password(db_session, user, "wrongpassword", "newpassword123")
