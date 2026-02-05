"""Tests for audit frontend functionality."""
import pytest
from datetime import date, timedelta
from src.services.audit_frontend_service import audit_frontend_service
from src.core.permissions import (
    AuditPermission,
    has_audit_permission,
    redact_sensitive_fields,
    get_audit_permissions,
)


class TestAuditPermissions:
    """Tests for audit permission system."""

    def test_admin_has_all_permissions(self):
        """Admin should have VIEW_ALL and EXPORT."""
        perms = get_audit_permissions("admin")
        assert AuditPermission.VIEW_ALL in perms
        assert AuditPermission.EXPORT in perms

    def test_staff_has_view_own_only(self):
        """Staff should only have VIEW_OWN."""
        perms = get_audit_permissions("staff")
        assert AuditPermission.VIEW_OWN in perms
        assert AuditPermission.VIEW_ALL not in perms
        assert AuditPermission.EXPORT not in perms

    def test_officer_has_member_and_user_view(self):
        """Officer should have VIEW_MEMBERS and VIEW_USERS."""
        perms = get_audit_permissions("officer")
        assert AuditPermission.VIEW_MEMBERS in perms
        assert AuditPermission.VIEW_USERS in perms

    def test_member_has_no_permissions(self):
        """Regular members should have no audit access."""
        perms = get_audit_permissions("member")
        assert len(perms) == 0

    def test_organizer_has_view_own_and_members(self):
        """Organizer should have VIEW_OWN and VIEW_MEMBERS."""
        perms = get_audit_permissions("organizer")
        assert AuditPermission.VIEW_OWN in perms
        assert AuditPermission.VIEW_MEMBERS in perms


class TestSensitiveFieldRedaction:
    """Tests for field redaction."""

    def test_admin_sees_all_fields(self):
        """Admin should see sensitive fields unredacted."""
        data = {"name": "John", "ssn": "123-45-6789"}
        result = redact_sensitive_fields(data, "admin")
        assert result["ssn"] == "123-45-6789"

    def test_staff_sees_redacted_ssn(self):
        """Non-admin should see SSN redacted."""
        data = {"name": "John", "ssn": "123-45-6789"}
        result = redact_sensitive_fields(data, "staff")
        assert result["name"] == "John"
        assert result["ssn"] == "[REDACTED]"

    def test_multiple_sensitive_fields(self):
        """Multiple sensitive fields should all be redacted."""
        data = {
            "name": "John",
            "ssn": "123-45-6789",
            "bank_account": "9876543210",
            "password_hash": "abc123",
        }
        result = redact_sensitive_fields(data, "officer")
        assert result["name"] == "John"
        assert result["ssn"] == "[REDACTED]"
        assert result["bank_account"] == "[REDACTED]"
        assert result["password_hash"] == "[REDACTED]"

    def test_none_input_returns_none(self):
        """None input should return None."""
        result = redact_sensitive_fields(None, "staff")
        assert result is None

    def test_nested_dict_redaction(self):
        """Nested dictionaries should have sensitive fields redacted."""
        data = {
            "user": {
                "name": "John",
                "password": "secret123"
            },
            "email": "john@test.com"
        }
        result = redact_sensitive_fields(data, "staff")
        assert result["user"]["name"] == "John"
        assert result["user"]["password"] == "[REDACTED]"
        assert result["email"] == "john@test.com"


class TestAuditFrontendService:
    """Tests for AuditFrontendService."""

    def test_get_action_types(self):
        """Should return all action types."""
        actions = audit_frontend_service.get_action_types()
        assert "CREATE" in actions
        assert "READ" in actions
        assert "UPDATE" in actions
        assert "DELETE" in actions
        assert "BULK_READ" in actions

    def test_get_primary_role_admin(self, test_user):
        """Should return admin as primary role for admin user."""
        primary = audit_frontend_service._get_primary_role(test_user)
        assert primary == "admin"

    def test_get_available_tables_returns_list(self, test_user):
        """Should return a list of table names."""
        tables = audit_frontend_service.get_available_tables(test_user)
        assert isinstance(tables, list)
        assert "members" in tables
        assert "users" in tables


class TestAuditFrontendAPI:
    """Tests for audit frontend API endpoints."""

    def test_audit_page_requires_auth(self, client):
        """Audit logs page requires authentication - redirects to login."""
        # TestClient follows redirects by default, so we get login page (200 OK)
        # To verify auth protection, check that we land on login page
        response = client.get("/admin/audit-logs")
        assert response.status_code == 200
        assert b"Login" in response.content or b"login" in response.content

    def test_export_endpoint_exists(self, client):
        """Export endpoint requires authentication - redirects to login."""
        response = client.get("/admin/audit-logs/export")
        assert response.status_code == 200
        assert b"Login" in response.content or b"login" in response.content

    def test_detail_endpoint_exists(self, client):
        """Detail endpoint requires authentication - redirects to login."""
        response = client.get("/admin/audit-logs/detail/1")
        assert response.status_code == 200
        assert b"Login" in response.content or b"login" in response.content

    def test_search_endpoint_exists(self, client):
        """Search endpoint requires authentication - redirects to login."""
        response = client.get("/admin/audit-logs/search")
        assert response.status_code == 200
        assert b"Login" in response.content or b"login" in response.content

    def test_entity_history_endpoint_exists(self, client):
        """Entity history endpoint requires authentication - redirects to login."""
        response = client.get("/admin/audit-logs/entity/members/1")
        assert response.status_code == 200
        assert b"Login" in response.content or b"login" in response.content
