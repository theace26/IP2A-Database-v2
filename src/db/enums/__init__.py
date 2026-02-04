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
    # Phase 2
    SALTingActivityType,
    SALTingOutcome,
    BenevolenceReason,
    BenevolenceStatus,
    BenevolenceReviewLevel,
    BenevolenceReviewDecision,
    GrievanceStep,
    GrievanceStatus,
    GrievanceStepOutcome,
)

from src.db.enums.auth_enums import (
    RoleType,
    TokenType,
)

from src.db.enums.training_enums import (
    StudentStatus,
    CourseEnrollmentStatus,
    SessionAttendanceStatus,
    GradeType,
    CertificationType,
    CertificationStatus,
    CourseType,
)

from src.db.enums.dues_enums import (
    DuesPaymentMethod,
    DuesPaymentStatus,
    DuesAdjustmentType,
    AdjustmentStatus,
)

from src.db.enums.grant_enums import (
    GrantStatus,
    GrantEnrollmentStatus,
    GrantOutcome,
)

from src.db.enums.phase7_enums import (
    # Book/Registration enums
    BookClassification,
    BookRegion,
    RegistrationStatus,
    RegistrationAction,
    ExemptReason,
    RolloffReason,
    NoCheckMarkReason,
    # Labor request/dispatch enums
    LaborRequestStatus,
    BidStatus,
    DispatchMethod,
    DispatchStatus,
    DispatchType,
    TermReason,
    JobClass,
    AgreementType,
    # Member enums
    MemberType,
    ReferralStatus,
    # Transaction enums
    ActivityCode,
    PaymentSource,
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
    # Phase 2 enums
    "SALTingActivityType",
    "SALTingOutcome",
    "BenevolenceReason",
    "BenevolenceStatus",
    "BenevolenceReviewLevel",
    "BenevolenceReviewDecision",
    "GrievanceStep",
    "GrievanceStatus",
    "GrievanceStepOutcome",
    # Auth enums
    "RoleType",
    "TokenType",
    # Training enums
    "StudentStatus",
    "CourseEnrollmentStatus",
    "SessionAttendanceStatus",
    "GradeType",
    "CertificationType",
    "CertificationStatus",
    "CourseType",
    # Dues enums
    "DuesPaymentMethod",
    "DuesPaymentStatus",
    "DuesAdjustmentType",
    "AdjustmentStatus",
    # Grant enums
    "GrantStatus",
    "GrantEnrollmentStatus",
    "GrantOutcome",
    # Phase 7 - Referral & Dispatch enums
    "BookClassification",
    "BookRegion",
    "RegistrationStatus",
    "RegistrationAction",
    "ExemptReason",
    "RolloffReason",
    "NoCheckMarkReason",
    "LaborRequestStatus",
    "BidStatus",
    "DispatchMethod",
    "DispatchStatus",
    "DispatchType",
    "TermReason",
    "JobClass",
    "AgreementType",
    "MemberType",
    "ReferralStatus",
    "ActivityCode",
    "PaymentSource",
]
