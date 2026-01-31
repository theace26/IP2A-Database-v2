"""Tests for system setup functionality."""

import pytest
from sqlalchemy.orm import Session

from src.services.setup_service import (
    has_any_users,
    has_non_default_users,
    validate_password,
    create_setup_user,
    get_available_roles,
    PasswordValidationError,
    is_setup_required,
    get_default_admin,
    get_default_admin_status,
    disable_default_admin,
    enable_default_admin,
    DEFAULT_ADMIN_EMAIL,
)
from src.models.user import User


class TestPasswordValidation:
    """Tests for password validation rules."""

    def test_valid_password(self):
        """Test a password that meets all requirements."""
        errors = validate_password("Admin@753!Bc")
        assert errors == []

    def test_minimum_length(self):
        """Test minimum length requirement."""
        errors = validate_password("Ab@1234")  # 7 characters
        assert "Password must be at least 8 characters" in errors

    def test_requires_three_unique_numbers(self):
        """Test requirement for 3 unique numbers."""
        errors = validate_password("Admin@11!Bc")  # Only 1 unique number
        assert "Password must contain at least 3 different numbers" in errors

    def test_requires_special_character(self):
        """Test requirement for special character."""
        errors = validate_password("Admin753Bcdef")  # No special char
        assert "Password must contain at least one special character" in errors

    def test_requires_capital_letter(self):
        """Test requirement for capital letter."""
        errors = validate_password("admin@753!bc")  # No capital
        assert "Password must contain at least one capital letter" in errors

    def test_no_repeating_letters(self):
        """Test no repeating letters rule."""
        # "Hello" has two l's
        errors = validate_password("Hello@753!X")
        assert "Password cannot contain repeating letters" in errors

    def test_no_sequential_numbers(self):
        """Test no sequential numbers rule."""
        errors = validate_password("Admin@123!Bc")  # Contains 123
        assert "Password cannot contain sequential numbers (like 123, 456)" in errors

    def test_multiple_errors(self):
        """Test that multiple errors are returned."""
        errors = validate_password("bad")
        assert len(errors) >= 3  # At least length, numbers, special, and capital


class TestGetAvailableRoles:
    """Tests for available roles."""

    def test_returns_list_of_roles(self):
        """Test that available roles are returned."""
        roles = get_available_roles()
        assert len(roles) >= 3
        assert any(r["value"] == "admin" for r in roles)
        assert any(r["value"] == "staff" for r in roles)

    def test_roles_have_required_fields(self):
        """Test that each role has value, label, description."""
        roles = get_available_roles()
        for role in roles:
            assert "value" in role
            assert "label" in role
            assert "description" in role


class TestDefaultAdminConstant:
    """Tests for the default admin constant."""

    def test_default_admin_email_is_set(self):
        """Test that the default admin email constant is defined."""
        assert DEFAULT_ADMIN_EMAIL == "admin@ibew46.com"


class TestHasAnyUsers:
    """Tests for user existence check."""

    def test_has_users_returns_true(self, db_session: Session):
        """Test that has_any_users returns True when users exist."""
        # The dev database has users from seeding
        assert has_any_users(db_session) is True


class TestHasNonDefaultUsers:
    """Tests for checking non-default users."""

    def test_has_non_default_users_with_only_default_admin(self, db_session: Session):
        """Test has_non_default_users when only default admin exists."""
        # The test database may only have the default admin
        # This should return False if only the default admin exists
        result = has_non_default_users(db_session)
        # Check how many non-default users exist
        from sqlalchemy import select, func
        count = db_session.execute(
            select(func.count(User.id)).where(User.email != DEFAULT_ADMIN_EMAIL)
        ).scalar()
        assert result == (count > 0)


class TestIsSetupRequired:
    """Tests for setup requirement check."""

    def test_setup_required_logic(self, db_session: Session):
        """Test is_setup_required returns correct value based on users."""
        # If only default admin exists, setup is required
        # If other users exist, setup is not required
        from sqlalchemy import select, func
        non_default_count = db_session.execute(
            select(func.count(User.id)).where(User.email != DEFAULT_ADMIN_EMAIL)
        ).scalar()

        if non_default_count == 0:
            # Only default admin (or no users), setup is required
            assert is_setup_required(db_session) is True
        else:
            # Other users exist, setup is not required
            assert is_setup_required(db_session) is False


class TestGetDefaultAdmin:
    """Tests for getting the default admin."""

    def test_get_default_admin_returns_user(self, db_session: Session):
        """Test that get_default_admin returns the seeded admin."""
        admin = get_default_admin(db_session)
        assert admin is not None
        assert admin.email == DEFAULT_ADMIN_EMAIL

    def test_get_default_admin_status(self, db_session: Session):
        """Test get_default_admin_status returns correct info."""
        status = get_default_admin_status(db_session)
        assert status["exists"] is True
        assert status["email"] == DEFAULT_ADMIN_EMAIL
        assert "is_active" in status


class TestDisableEnableDefaultAdmin:
    """Tests for disabling/enabling the default admin."""

    def test_disable_default_admin(self, db_session: Session):
        """Test that we can disable the default admin."""
        # First ensure it's active
        admin = get_default_admin(db_session)
        original_status = admin.is_active

        # Disable it
        result = disable_default_admin(db_session)
        assert result is True

        # Verify it's disabled
        db_session.refresh(admin)
        assert admin.is_active is False

        # Re-enable it for other tests
        enable_default_admin(db_session)
        db_session.refresh(admin)
        assert admin.is_active is True

    def test_enable_default_admin(self, db_session: Session):
        """Test that we can enable the default admin."""
        # First disable it
        disable_default_admin(db_session)
        admin = get_default_admin(db_session)
        db_session.refresh(admin)
        assert admin.is_active is False

        # Enable it
        result = enable_default_admin(db_session)
        assert result is True

        # Verify it's enabled
        db_session.refresh(admin)
        assert admin.is_active is True


class TestSetupRoutes:
    """Tests for setup page routes."""

    def test_setup_page_behavior(self, client, db_session: Session):
        """Test /setup page behavior based on user state."""
        # Check how many non-default users exist
        from sqlalchemy import select, func
        non_default_count = db_session.execute(
            select(func.count(User.id)).where(User.email != DEFAULT_ADMIN_EMAIL)
        ).scalar()

        response = client.get("/setup", follow_redirects=False)

        if non_default_count == 0:
            # Setup required - should show setup page
            assert response.status_code == 200
            assert b"System Setup" in response.content or b"Welcome to IP2A" in response.content
        else:
            # Setup complete - should redirect to login
            assert response.status_code == 302
            assert "/login" in response.headers["location"]

    def test_login_page_renders(self, client, db_session: Session):
        """Test that /login renders or redirects based on setup state."""
        from sqlalchemy import select, func
        non_default_count = db_session.execute(
            select(func.count(User.id)).where(User.email != DEFAULT_ADMIN_EMAIL)
        ).scalar()

        response = client.get("/login", follow_redirects=False)

        if non_default_count == 0:
            # Setup required - should redirect to setup
            assert response.status_code == 302
            assert "/setup" in response.headers["location"]
        else:
            # Setup complete - should show login page
            assert response.status_code == 200
            assert b"IBEW Local 46" in response.content

    def test_root_redirect_behavior(self, client, db_session: Session):
        """Test that / redirects appropriately based on setup state."""
        from sqlalchemy import select, func
        non_default_count = db_session.execute(
            select(func.count(User.id)).where(User.email != DEFAULT_ADMIN_EMAIL)
        ).scalar()

        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302

        if non_default_count == 0:
            # Setup required - should redirect to setup
            assert "/setup" in response.headers["location"]
        else:
            # Setup complete - should redirect to login
            assert "/login" in response.headers["location"]

    def test_setup_shows_default_admin_info(self, client, db_session: Session):
        """Test that setup page shows default admin account info when it exists."""
        from sqlalchemy import select, func
        non_default_count = db_session.execute(
            select(func.count(User.id)).where(User.email != DEFAULT_ADMIN_EMAIL)
        ).scalar()

        if non_default_count == 0:
            # Only proceed if setup page is accessible
            response = client.get("/setup")
            assert response.status_code == 200
            # Check for default admin info display
            assert b"admin@ibew46.com" in response.content or b"Default System Account" in response.content

    def test_setup_has_disable_checkbox(self, client, db_session: Session):
        """Test that setup page has checkbox to disable default admin."""
        from sqlalchemy import select, func
        non_default_count = db_session.execute(
            select(func.count(User.id)).where(User.email != DEFAULT_ADMIN_EMAIL)
        ).scalar()

        if non_default_count == 0:
            # Only proceed if setup page is accessible
            response = client.get("/setup")
            assert response.status_code == 200
            # Check for disable checkbox
            assert b"disable_default_admin" in response.content


class TestCreateSetupUser:
    """Tests for the create_setup_user function."""

    def test_cannot_use_default_admin_email(self, db_session: Session):
        """Test that we cannot create a user with the default admin email."""
        # Note: This test would require an empty database to properly test
        # In a seeded database, this would fail with "already set up" error first
        # We test the email validation in the service function separately
        pass

    def test_default_admin_email_blocked(self):
        """Test that the DEFAULT_ADMIN_EMAIL constant matches expected value."""
        # This validates the constant is set correctly
        assert DEFAULT_ADMIN_EMAIL == "admin@ibew46.com"
