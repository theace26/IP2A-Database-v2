"""Permission constants for role-based access control."""
from enum import Enum
from typing import Dict, List


class AuditPermission(str, Enum):
    """Audit-specific permissions."""
    VIEW_OWN = "audit:view_own"              # View entities user touched
    VIEW_MEMBERS = "audit:view_members"       # View all member-related audits
    VIEW_USERS = "audit:view_users"           # View user account audits
    VIEW_ALL = "audit:view_all"               # View everything
    EXPORT = "audit:export"                   # Export audit reports


# Map roles to their audit permissions
ROLE_AUDIT_PERMISSIONS: Dict[str, List[AuditPermission]] = {
    "member": [],  # No audit access
    "staff": [AuditPermission.VIEW_OWN],
    "instructor": [AuditPermission.VIEW_OWN],
    "organizer": [AuditPermission.VIEW_OWN, AuditPermission.VIEW_MEMBERS],
    "officer": [AuditPermission.VIEW_MEMBERS, AuditPermission.VIEW_USERS],
    "admin": [
        AuditPermission.VIEW_ALL,
        AuditPermission.VIEW_USERS,
        AuditPermission.EXPORT
    ],
}


def get_audit_permissions(role: str) -> List[AuditPermission]:
    """Get audit permissions for a role."""
    return ROLE_AUDIT_PERMISSIONS.get(role, [])


def has_audit_permission(role: str, permission: AuditPermission) -> bool:
    """Check if a role has a specific audit permission."""
    return permission in get_audit_permissions(role)


# Sensitive fields that should be redacted for non-admin users
SENSITIVE_FIELDS = {
    "ssn",
    "social_security",
    "social_security_number",
    "bank_account",
    "bank_account_number",
    "routing_number",
    "password",
    "password_hash",
    "token_hash",
    "refresh_token",
    "api_key",
    "secret_key",
}


def redact_sensitive_fields(data: dict, user_role: str) -> dict:
    """
    Redact sensitive fields based on user role.
    Admin users see all fields unredacted.
    """
    if data is None:
        return None

    if user_role == "admin":
        return data  # Admins see everything

    redacted = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_FIELDS:
            redacted[key] = "[REDACTED]"
        elif isinstance(value, dict):
            redacted[key] = redact_sensitive_fields(value, user_role)
        else:
            redacted[key] = value

    return redacted
