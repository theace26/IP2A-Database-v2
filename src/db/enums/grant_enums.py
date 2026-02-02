"""Enums for grant tracking and compliance reporting."""

from enum import Enum


class GrantStatus(str, Enum):
    """Status of a grant."""
    PENDING = "pending"           # Awaiting approval/start
    ACTIVE = "active"             # Currently active
    COMPLETED = "completed"       # Successfully completed
    CLOSED = "closed"             # Closed (any reason)
    SUSPENDED = "suspended"       # Temporarily suspended


class GrantEnrollmentStatus(str, Enum):
    """Status of student enrollment in a grant."""
    ENROLLED = "enrolled"         # Initially enrolled
    ACTIVE = "active"             # Currently participating
    COMPLETED = "completed"       # Completed grant requirements
    WITHDRAWN = "withdrawn"       # Voluntarily withdrew
    DROPPED = "dropped"           # Dropped due to non-participation


class GrantOutcome(str, Enum):
    """Outcome for grant compliance reporting."""
    COMPLETED_PROGRAM = "completed_program"         # Finished training program
    OBTAINED_CREDENTIAL = "obtained_credential"     # Got certification/credential
    ENTERED_APPRENTICESHIP = "entered_apprenticeship"  # Joined apprenticeship
    OBTAINED_EMPLOYMENT = "obtained_employment"     # Got job in trade
    CONTINUED_EDUCATION = "continued_education"     # Continued to further education
    WITHDRAWN = "withdrawn"                         # Left program
    OTHER = "other"                                 # Other outcome
