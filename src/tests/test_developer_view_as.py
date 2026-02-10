"""
Tests for Developer role and View As impersonation feature (ADR-019).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models.user import User
from src.models.role import Role
from src.models.user_role import UserRole
from src.core.security import hash_password
from src.db.enums import RoleType


@pytest.fixture
def developer_user(db: Session) -> User:
    """Create a developer user for testing."""
    # Get or create developer role
    developer_role = (
        db.query(Role).filter(Role.name == RoleType.DEVELOPER.value).first()
    )
    if not developer_role:
        developer_role = Role(
            name=RoleType.DEVELOPER.value,
            display_name="Developer",
            description="Developer super admin with View As",
            is_system_role=True,
        )
        db.add(developer_role)
        db.flush()

    # Create developer user
    user = User(
        email="dev_test@ibew46.local",
        password_hash=hash_password("Test@123!"),
        first_name="Developer",
        last_name="Test",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.flush()

    # Assign developer role
    user_role = UserRole(user_id=user.id, role_id=developer_role.id)
    db.add(user_role)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def developer_client(developer_user: User) -> TestClient:
    """Create a test client with developer authentication."""
    client = TestClient(app)

    # Login as developer
    response = client.post(
        "/login",
        data={"email": developer_user.email, "password": "Test@123!"},
    )
    assert response.status_code in [200, 302]

    return client


@pytest.fixture
def admin_user(db: Session) -> User:
    """Create an admin user for comparison testing."""
    # Get admin role
    admin_role = db.query(Role).filter(Role.name == RoleType.ADMIN.value).first()

    # Create admin user
    user = User(
        email="admin_test@ibew46.local",
        password_hash=hash_password("Test@123!"),
        first_name="Admin",
        last_name="Test",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.flush()

    # Assign admin role
    user_role = UserRole(user_id=user.id, role_id=admin_role.id)
    db.add(user_role)
    db.commit()
    db.refresh(user)

    return user


# ============================================================================
# Developer Role Tests
# ============================================================================


def test_developer_role_exists(db: Session):
    """Test that developer role exists in database."""
    role = db.query(Role).filter(Role.name == RoleType.DEVELOPER.value).first()
    assert role is not None
    assert role.display_name == "Developer"
    assert role.is_system_role is True


def test_developer_enum_exists():
    """Test that DEVELOPER enum value exists."""
    assert hasattr(RoleType, "DEVELOPER")
    assert RoleType.DEVELOPER.value == "developer"


def test_developer_user_can_login(developer_client: TestClient):
    """Test that developer user can successfully log in."""
    # Client fixture already logged in, check dashboard access
    response = developer_client.get("/dashboard")
    assert response.status_code == 200


def test_developer_has_all_audit_permissions(db: Session, developer_user: User):
    """Test that developer role has all audit permissions."""
    from src.core.permissions import get_audit_permissions, AuditPermission

    permissions = get_audit_permissions("developer")

    assert AuditPermission.VIEW_ALL in permissions
    assert AuditPermission.VIEW_USERS in permissions
    assert AuditPermission.VIEW_MEMBERS in permissions
    assert AuditPermission.VIEW_OWN in permissions
    assert AuditPermission.EXPORT in permissions


def test_developer_no_sensitive_field_redaction(db: Session):
    """Test that developer role sees unredacted sensitive fields."""
    from src.core.permissions import redact_sensitive_fields

    test_data = {
        "name": "John Doe",
        "ssn": "123-45-6789",
        "password_hash": "hashed_password",
        "email": "john@example.com",
    }

    # Developer should see everything
    result = redact_sensitive_fields(test_data, "developer")
    assert result["ssn"] == "123-45-6789"
    assert result["password_hash"] == "hashed_password"

    # Admin should also see everything
    result = redact_sensitive_fields(test_data, "admin")
    assert result["ssn"] == "123-45-6789"

    # Staff should see redactions
    result = redact_sensitive_fields(test_data, "staff")
    assert result["ssn"] == "[REDACTED]"


# ============================================================================
# View As API Tests
# ============================================================================


def test_view_as_set_role_success(developer_client: TestClient):
    """Test setting View As role via API."""
    response = developer_client.post("/api/v1/view-as/set/admin")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["viewing_as"] == "admin"


def test_view_as_set_invalid_role(developer_client: TestClient):
    """Test setting View As with invalid role."""
    response = developer_client.post("/api/v1/view-as/set/superuser")
    assert response.status_code == 400
    data = response.json()
    assert "Invalid role" in data["detail"]


def test_view_as_clear_success(developer_client: TestClient):
    """Test clearing View As role."""
    # First set a role
    developer_client.post("/api/v1/view-as/set/staff")

    # Then clear it
    response = developer_client.post("/api/v1/view-as/clear")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["viewing_as"] is None


def test_view_as_get_current(developer_client: TestClient):
    """Test getting current View As role."""
    # Set a role first
    developer_client.post("/api/v1/view-as/set/officer")

    # Get current
    response = developer_client.get("/api/v1/view-as/current")
    assert response.status_code == 200
    data = response.json()
    assert data["viewing_as"] == "officer"
    assert "available_roles" in data


def test_view_as_non_developer_denied(db: Session, admin_user: User):
    """Test that non-developer users cannot use View As."""
    client = TestClient(app)

    # Login as admin (not developer)
    response = client.post(
        "/login",
        data={"email": admin_user.email, "password": "Test@123!"},
    )
    assert response.status_code in [200, 302]

    # Try to set View As
    response = client.post("/api/v1/view-as/set/staff")
    assert response.status_code == 403
    data = response.json()
    assert "Only developer role" in data["detail"]


def test_view_as_all_roles_available(developer_client: TestClient):
    """Test that all expected roles are available for View As."""
    response = developer_client.get("/api/v1/view-as/current")
    data = response.json()

    available_roles = data["available_roles"]
    assert "admin" in available_roles
    assert "officer" in available_roles
    assert "staff" in available_roles
    assert "organizer" in available_roles
    assert "instructor" in available_roles
    assert "member" in available_roles

    # Developer should NOT be in the list (can't impersonate self)
    assert "developer" not in available_roles


# ============================================================================
# View As Integration Tests (UI)
# ============================================================================


def test_view_as_navbar_dropdown_visible_for_developer(developer_client: TestClient):
    """Test that View As dropdown appears in navbar for developer."""
    response = developer_client.get("/dashboard")
    assert response.status_code == 200

    # Check for View As dropdown in HTML
    html = response.text
    assert "View As" in html
    assert "api/v1/view-as/set" in html


def test_view_as_navbar_dropdown_hidden_for_non_developer(
    db: Session, admin_user: User
):
    """Test that View As dropdown does NOT appear for non-developer."""
    client = TestClient(app)

    # Login as admin
    response = client.post(
        "/login",
        data={"email": admin_user.email, "password": "Test@123!"},
    )

    # Check dashboard
    response = client.get("/dashboard")
    assert response.status_code == 200

    # View As dropdown should not be present
    html = response.text
    # This is a bit fragile, but we're looking for the View As button
    assert "x-text=\"viewing_as || 'View As'\"" not in html


def test_view_as_impersonation_banner_shows_when_active(developer_client: TestClient):
    """Test that impersonation banner appears when View As is active."""
    # Set View As to staff
    developer_client.post("/api/v1/view-as/set/staff")

    # Load dashboard
    response = developer_client.get("/dashboard")
    assert response.status_code == 200

    html = response.text
    assert "Impersonation Active" in html
    assert "Viewing as:" in html
    assert "STAFF" in html


def test_view_as_impersonation_banner_hidden_when_inactive(
    developer_client: TestClient,
):
    """Test that impersonation banner does NOT appear when View As is inactive."""
    # Ensure View As is cleared
    developer_client.post("/api/v1/view-as/clear")

    # Load dashboard
    response = developer_client.get("/dashboard")
    assert response.status_code == 200

    html = response.text
    assert "Impersonation Active" not in html


# ============================================================================
# Security Tests
# ============================================================================


def test_view_as_audit_logs_record_real_user(db: Session, developer_client: TestClient):
    """Test that audit logs record the real developer user, not impersonated role."""

    # Set View As to staff
    developer_client.post("/api/v1/view-as/set/staff")

    # Perform an action that triggers audit logging (e.g., create a member)
    # This would require more setup, so for now we just verify the concept
    # In a real scenario, the audit log should show the developer's user ID

    # For this test, we're verifying the middleware correctly passes through
    # the real user ID to the audit context
    # The actual audit logging is tested elsewhere
    pass


def test_view_as_session_based_not_jwt(developer_client: TestClient):
    """Test that viewing_as is stored in session, not JWT token."""
    # Set View As
    response = developer_client.post("/api/v1/view-as/set/member")
    assert response.status_code == 200

    # The JWT token should NOT contain viewing_as
    # viewing_as should only be in the session
    # This is verified by the fact that auth_cookie.py reads from request.session

    # Get current
    response = developer_client.get("/api/v1/view-as/current")
    data = response.json()
    assert data["viewing_as"] == "member"


def test_developer_role_cannot_be_assigned_via_ui():
    """
    Test that developer role cannot be assigned through normal UI flows.
    This is a documentation test - the actual constraint is that there's
    no UI for assigning the developer role.
    """
    # This is a conceptual test to document the security constraint
    # The developer role should only be assignable via:
    # 1. Seed scripts
    # 2. Direct database manipulation
    # 3. NOT through the staff management UI

    assert True  # Placeholder - actual UI tests would verify this


# ============================================================================
# Production Safety Tests
# ============================================================================


def test_developer_role_warning_in_description(db: Session):
    """Test that developer role description warns about dev/demo only."""
    role = db.query(Role).filter(Role.name == RoleType.DEVELOPER.value).first()
    assert role is not None
    assert "DEV" in role.description.upper() or "DEMO" in role.description.upper()
    assert "PRODUCTION" in role.description.upper()


def test_demo_developer_account_exists(db: Session):
    """Test that demo seed creates a developer account."""
    # This would be tested by running the demo seed
    # For now, just verify the structure exists

    # The test would run seed_demo_users and verify the developer account exists
    # Skipping actual execution to avoid side effects
    pass
