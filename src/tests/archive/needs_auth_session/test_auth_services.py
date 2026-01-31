"""Tests for authentication services."""

import uuid

from src.models.user import User
from src.models.role import Role
from src.services.user_service import (
    create_user,
    get_user_by_email,
    update_user,
)
from src.services.role_service import (
    create_role,
    get_role_by_name,
)
from src.services.user_role_service import (
    assign_role,
    get_user_roles,
    remove_role,
)
from src.schemas.user import UserCreate, UserUpdate
from src.schemas.role import RoleCreate
from src.schemas.user_role import UserRoleCreate


class TestUserService:
    """Tests for user service."""

    def test_create_user(self, db_session):
        """Test creating a user through service."""
        email = f"service_{uuid.uuid4().hex[:8]}@example.com"
        user_data = UserCreate(
            email=email,
            first_name="Service",
            last_name="Test",
            password="securepassword123",
        )

        user = create_user(db_session, user_data, password_hash="hashed_pw")

        assert user.id is not None
        assert user.email == email
        assert user.password_hash == "hashed_pw"

    def test_get_user_by_email(self, db_session):
        """Test finding user by email."""
        email = f"find_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash="hash",
            first_name="Find",
            last_name="Me",
        )
        db_session.add(user)
        db_session.commit()

        found = get_user_by_email(db_session, email)
        assert found is not None
        assert found.id == user.id

        not_found = get_user_by_email(db_session, "notexist@example.com")
        assert not_found is None

    def test_update_user(self, db_session):
        """Test updating a user."""
        email = f"update_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash="hash",
            first_name="Before",
            last_name="Update",
        )
        db_session.add(user)
        db_session.commit()

        update_data = UserUpdate(first_name="After")
        updated = update_user(db_session, user, update_data)

        assert updated.first_name == "After"
        assert updated.last_name == "Update"  # Unchanged


class TestRoleService:
    """Tests for role service."""

    def test_create_role(self, db_session):
        """Test creating a role through service."""
        role_name = f"custom_role_{uuid.uuid4().hex[:8]}"
        role_data = RoleCreate(
            name=role_name,
            display_name="Custom Role",
            description="A custom role",
        )

        role = create_role(db_session, role_data)

        assert role.id is not None
        assert role.name == role_name.lower()  # Lowercased

    def test_get_role_by_name(self, db_session):
        """Test finding role by name."""
        role_name = f"findme_{uuid.uuid4().hex[:8]}"
        role = Role(name=role_name, display_name="Find Me")
        db_session.add(role)
        db_session.commit()

        found = get_role_by_name(db_session, role_name)
        assert found is not None

        # Case insensitive
        found_upper = get_role_by_name(db_session, role_name.upper())
        assert found_upper is not None


class TestUserRoleService:
    """Tests for user role service."""

    def test_assign_and_remove_role(self, db_session):
        """Test assigning and removing roles."""
        email = f"roleop_{uuid.uuid4().hex[:8]}@example.com"
        role_name = f"testassign_{uuid.uuid4().hex[:8]}"
        user = User(
            email=email,
            password_hash="hash",
            first_name="Role",
            last_name="Op",
        )
        role = Role(name=role_name, display_name="Test Assign")
        db_session.add(user)
        db_session.add(role)
        db_session.commit()

        # Assign
        assignment = UserRoleCreate(
            user_id=user.id,
            role_id=role.id,
            assigned_by="admin",
        )
        user_role = assign_role(db_session, assignment)
        assert user_role.id is not None

        # Verify
        roles = get_user_roles(db_session, user.id)
        assert len(roles) == 1

        # Remove
        remove_role(db_session, user_role)
        roles_after = get_user_roles(db_session, user.id)
        assert len(roles_after) == 0
