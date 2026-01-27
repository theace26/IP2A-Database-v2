"""
Database enums - consolidated exports.

All enums are defined in src/db/enums/ to avoid circular imports.
Models should import from here:
    from src.db.enums import CohortStatus, MemberStatus
"""

# Import from local enum files (no circular dependency)
from src.db.enums.base_enums import (
    LocationType,
    EnrollmentStatus,
    AttendanceStatus,
    CohortStatus,
    CredentialStatus,
    PaymentMethod,
    RateType,
    ApplicationStatus,
)

from src.db.enums.organization_enums import (
    OrganizationType,
    MemberStatus,
    MemberClassification,
    SaltingScore,
    AuditAction,
)

__all__ = [
    # Base enums (education/training)
    "LocationType",
    "EnrollmentStatus",
    "AttendanceStatus",
    "CohortStatus",
    "CredentialStatus",
    "PaymentMethod",
    "RateType",
    "ApplicationStatus",
    # Organization enums (union operations)
    "OrganizationType",
    "MemberStatus",
    "MemberClassification",
    "SaltingScore",
    "AuditAction",
]
