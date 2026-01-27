"""
Enumeration types for the IP2A Database.

Using Python enums that inherit from (str, enum.Enum) allows:
- Database storage as strings (human-readable)
- Type safety in Python code
- Easy serialization to/from JSON APIs

Usage in models:
    from src.db.enums import LocationType

    type = Column(
        Enum(LocationType, name="location_type", create_constraint=True),
        nullable=False,
        default=LocationType.TRAINING_SITE,
    )
"""

import enum


class LocationType(str, enum.Enum):
    """Types of locations/facilities."""

    TRAINING_SITE = "training_site"
    SCHOOL = "school"
    OFFICE = "office"
    JOBSITE = "jobsite"
    VENDOR = "vendor"
    OTHER = "other"


class EnrollmentStatus(str, enum.Enum):
    """Status of a student's enrollment in a cohort/course."""

    ENROLLED = "enrolled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DROPPED = "dropped"
    WITHDRAWN = "withdrawn"
    DEFERRED = "deferred"


class AttendanceStatus(str, enum.Enum):
    """Attendance status for a class session."""

    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"
    EARLY_DEPARTURE = "early_departure"


class CohortStatus(str, enum.Enum):
    """Status of a cohort."""

    PLANNED = "planned"
    ENROLLING = "enrolling"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CredentialStatus(str, enum.Enum):
    """Status of a credential/certification."""

    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    RENEWED = "renewed"


class PaymentMethod(str, enum.Enum):
    """Payment methods for expenses."""

    CASH = "cash"
    CHECK = "check"
    CARD = "card"
    ACH = "ach"
    WIRE = "wire"
    GRANT = "grant"  # Paid directly from grant funds
    OTHER = "other"


class RateType(str, enum.Enum):
    """Pay rate types for instructors."""

    HOURLY = "hourly"
    DAILY = "daily"
    FLAT = "flat"  # Flat rate per course/cohort
    SALARY = "salary"


class ApplicationStatus(str, enum.Enum):
    """JATC application status progression."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEWED = "interviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WAITLISTED = "waitlisted"
    WITHDRAWN = "withdrawn"


# Future: IBEW Local 46 specific enums


class MemberStatus(str, enum.Enum):
    """IBEW member status (for future Local 46 integration)."""

    ACTIVE = "active"
    RETIRED = "retired"
    SUSPENDED = "suspended"
    WITHDRAWN = "withdrawn"
    DECEASED = "deceased"
    HONORARY = "honorary"


class MemberClassification(str, enum.Enum):
    """IBEW member classification (for future Local 46 integration)."""

    APPRENTICE = "apprentice"
    JOURNEYMAN = "journeyman"
    FOREMAN = "foreman"
    GENERAL_FOREMAN = "general_foreman"
    SUPERINTENDENT = "superintendent"
    CONTRACTOR = "contractor"
