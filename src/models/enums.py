"""
DEPRECATED: Enums have moved to src/db/enums/

This file exists for backwards compatibility only.
Please update imports to use:
    from src.db.enums import EnumName

This file will be removed in a future version.
"""

# Re-export everything from the new location (must be at top for E402)
from src.db.enums import (
    LocationType,
    EnrollmentStatus,
    AttendanceStatus,
    CohortStatus,
    CredentialStatus,
    PaymentMethod,
    RateType,
    ApplicationStatus,
    OrganizationType,
    MemberStatus,
    MemberClassification,
    SaltingScore,
    AuditAction,
)

import warnings

warnings.warn(
    "Importing from src.models.enums is deprecated. "
    "Use 'from src.db.enums import ...' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "LocationType",
    "EnrollmentStatus",
    "AttendanceStatus",
    "CohortStatus",
    "CredentialStatus",
    "PaymentMethod",
    "RateType",
    "ApplicationStatus",
    "OrganizationType",
    "MemberStatus",
    "MemberClassification",
    "SaltingScore",
    "AuditAction",
]
