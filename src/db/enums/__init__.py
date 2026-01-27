"""Database enums - consolidated exports."""

# Import from existing models/enums.py
from src.models.enums import (
    LocationType,
    EnrollmentStatus,
    AttendanceStatus,
    CohortStatus,
    CredentialStatus,
    PaymentMethod,
    RateType,
    ApplicationStatus,
)

# Import new organization enums
from src.db.enums.organization_enums import (
    OrganizationType,
    MemberStatus,
    MemberClassification,
    SaltingScore,
    AuditAction,
)

__all__ = [
    # Existing enums
    "LocationType",
    "EnrollmentStatus",
    "AttendanceStatus",
    "CohortStatus",
    "CredentialStatus",
    "PaymentMethod",
    "RateType",
    "ApplicationStatus",
    # New organization enums
    "OrganizationType",
    "MemberStatus",
    "MemberClassification",
    "SaltingScore",
    "AuditAction",
]
