import enum


class LocationType(str, enum.Enum):
    TRAINING_SITE = "training_site"
    SCHOOL = "school"
    OFFICE = "office"
    JOBSITE = "jobsite"
    OTHER = "other"


class EnrollmentStatus(str, enum.Enum):
    ENROLLED = "enrolled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DROPPED = "dropped"
    WITHDRAWN = "withdrawn"


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class CohortStatus(str, enum.Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CredentialStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CHECK = "check"
    CARD = "card"
    ACH = "ach"
    OTHER = "other"


class RateType(str, enum.Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    FLAT = "flat"
