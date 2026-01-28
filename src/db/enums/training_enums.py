"""Enums for pre-apprenticeship training system."""

from enum import Enum


class StudentStatus(str, Enum):
    """Student enrollment status."""
    APPLICANT = "applicant"           # Applied, not yet accepted
    ENROLLED = "enrolled"             # Currently in program
    ON_LEAVE = "on_leave"             # Temporary leave
    COMPLETED = "completed"           # Finished program
    DROPPED = "dropped"               # Dropped out
    DISMISSED = "dismissed"           # Removed from program


class CourseEnrollmentStatus(str, Enum):
    """Course enrollment status (training-specific)."""
    ENROLLED = "enrolled"             # Currently enrolled
    COMPLETED = "completed"           # Completed course
    WITHDRAWN = "withdrawn"           # Withdrew from course
    FAILED = "failed"                 # Did not pass
    INCOMPLETE = "incomplete"         # Did not finish


class SessionAttendanceStatus(str, Enum):
    """Class session attendance status (training-specific)."""
    PRESENT = "present"
    ABSENT = "absent"
    EXCUSED = "excused"
    LATE = "late"
    LEFT_EARLY = "left_early"


class GradeType(str, Enum):
    """Type of grade/assessment."""
    ASSIGNMENT = "assignment"
    QUIZ = "quiz"
    EXAM = "exam"
    PROJECT = "project"
    PARTICIPATION = "participation"
    FINAL = "final"


class CertificationType(str, Enum):
    """Type of certification."""
    OSHA_10 = "osha_10"
    OSHA_30 = "osha_30"
    FIRST_AID = "first_aid"
    CPR = "cpr"
    FORKLIFT = "forklift"
    AERIAL_LIFT = "aerial_lift"
    CONFINED_SPACE = "confined_space"
    HAZMAT = "hazmat"
    FLAGGER = "flagger"
    ELECTRICAL_TRAINEE = "electrical_trainee"
    OTHER = "other"


class CertificationStatus(str, Enum):
    """Certification status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class CourseType(str, Enum):
    """Type of course."""
    CORE = "core"                     # Required for all students
    ELECTIVE = "elective"             # Optional course
    REMEDIAL = "remedial"             # For students needing extra help
    ADVANCED = "advanced"             # Advanced topics
    CERTIFICATION = "certification"   # Certification prep
