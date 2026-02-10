"""Authentication and authorization enums."""

from enum import Enum


class RoleType(str, Enum):
    """Default system roles."""

    DEVELOPER = "developer"  # Level 255 - dev/demo only, never production
    ADMIN = "admin"
    OFFICER = "officer"
    STAFF = "staff"
    ORGANIZER = "organizer"
    INSTRUCTOR = "instructor"
    MEMBER = "member"


class TokenType(str, Enum):
    """Types of authentication tokens."""

    ACCESS = "access"
    REFRESH = "refresh"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
