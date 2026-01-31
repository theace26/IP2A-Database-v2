"""Tests for authentication models."""

import pytest
import uuid
from datetime import datetime, timedelta, timezone

from src.models.user import User
from src.models.role import Role
from src.models.user_role import UserRole
from src.models.refresh_token import RefreshToken


class TestUserModel:
    """Tests for User model."""

    def test_create_user(self, db_session):
        """Test creating a user."""
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash="hashed_password",
            first_name="Test",
            last_name="User",
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == email
        assert user.is_active is True
        assert user.is_verified is False
        assert user.full_name == "Test User"

    def test_user_email_unique(self, db_session):
        """Test that email must be unique."""
        email = f"same_{uuid.uuid4().hex[:8]}@example.com"
        user1 = User(
            email=email,
            password_hash="hash1",
            first_name="User",
            last_name="One",
        )
        db_session.add(user1)
        db_session.commit()

        user2 = User(
            email=email,
            password_hash="hash2",
            first_name="User",
            last_name="Two",
        )
        db_session.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_user_soft_delete(self, db_session):
        """Test soft delete functionality."""
        email = f"delete_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash="hash",
            first_name="Delete",
            last_name="Me",
        )
        db_session.add(user)
        db_session.commit()

        user.soft_delete()
        db_session.commit()

        assert user.deleted_at is not None


class TestRoleModel:
    """Tests for Role model."""

    def test_create_role(self, db_session):
        """Test creating a role."""
        role_name = f"test_role_{uuid.uuid4().hex[:8]}"
        role = Role(
            name=role_name,
            display_name="Test Role",
            description="A test role",
            is_system_role=False,
        )
        db_session.add(role)
        db_session.commit()

        assert role.id is not None
        assert role.name == role_name

    def test_role_name_unique(self, db_session):
        """Test that role name must be unique."""
        role_name = f"unique_role_{uuid.uuid4().hex[:8]}"
        role1 = Role(name=role_name, display_name="Role 1")
        db_session.add(role1)
        db_session.commit()

        role2 = Role(name=role_name, display_name="Role 2")
        db_session.add(role2)

        with pytest.raises(Exception):
            db_session.commit()


class TestUserRoleModel:
    """Tests for UserRole model."""

    def test_assign_role_to_user(self, db_session):
        """Test assigning a role to a user."""
        email = f"roletest_{uuid.uuid4().hex[:8]}@example.com"
        role_name = f"member_{uuid.uuid4().hex[:8]}"
        user = User(
            email=email,
            password_hash="hash",
            first_name="Role",
            last_name="Test",
        )
        role = Role(name=role_name, display_name="Member")

        db_session.add(user)
        db_session.add(role)
        db_session.commit()

        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            assigned_by="admin@example.com",
        )
        db_session.add(user_role)
        db_session.commit()

        assert user_role.id is not None
        assert user.has_role(role_name)

    def test_user_role_unique_constraint(self, db_session):
        """Test that user can only have each role once."""
        email = f"unique_{uuid.uuid4().hex[:8]}@example.com"
        role_name = f"single_role_{uuid.uuid4().hex[:8]}"
        user = User(
            email=email,
            password_hash="hash",
            first_name="Unique",
            last_name="User",
        )
        role = Role(name=role_name, display_name="Single Role")

        db_session.add(user)
        db_session.add(role)
        db_session.commit()

        ur1 = UserRole(user_id=user.id, role_id=role.id)
        db_session.add(ur1)
        db_session.commit()

        ur2 = UserRole(user_id=user.id, role_id=role.id)
        db_session.add(ur2)

        with pytest.raises(Exception):
            db_session.commit()


class TestRefreshTokenModel:
    """Tests for RefreshToken model."""

    def test_create_refresh_token(self, db_session):
        """Test creating a refresh token."""
        email = f"token_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash="hash",
            first_name="Token",
            last_name="User",
        )
        db_session.add(user)
        db_session.commit()

        token = RefreshToken(
            user_id=user.id,
            token_hash=f"abc123hash_{uuid.uuid4().hex[:8]}",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db_session.add(token)
        db_session.commit()

        assert token.id is not None
        assert token.is_valid is True
        assert token.is_expired is False
        assert token.is_revoked is False

    def test_expired_token(self, db_session):
        """Test expired token detection."""
        email = f"expired_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash="hash",
            first_name="Expired",
            last_name="User",
        )
        db_session.add(user)
        db_session.commit()

        token = RefreshToken(
            user_id=user.id,
            token_hash=f"expiredhash_{uuid.uuid4().hex[:8]}",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db_session.add(token)
        db_session.commit()

        assert token.is_expired is True
        assert token.is_valid is False

    def test_revoked_token(self, db_session):
        """Test revoked token detection."""
        email = f"revoked_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash="hash",
            first_name="Revoked",
            last_name="User",
        )
        db_session.add(user)
        db_session.commit()

        token = RefreshToken(
            user_id=user.id,
            token_hash=f"revokedhash_{uuid.uuid4().hex[:8]}",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            is_revoked=True,
            revoked_at=datetime.now(timezone.utc),
        )
        db_session.add(token)
        db_session.commit()

        assert token.is_revoked is True
        assert token.is_valid is False
