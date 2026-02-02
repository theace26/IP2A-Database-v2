"""
Pydantic schemas for IP2A Database v2
"""

# Student schemas
from src.schemas.student import (
    StudentBase,
    StudentCreate,
    StudentUpdate,
    StudentRead,
)

# Instructor schemas
from src.schemas.instructor import (
    InstructorBase,
    InstructorCreate,
    InstructorUpdate,
    InstructorRead,
)

# Cohort schemas
from src.schemas.cohort import (
    CohortBase,
    CohortCreate,
    CohortUpdate,
    CohortRead,
)

# Location schemas
from src.schemas.location import (
    LocationBase,
    LocationCreate,
    LocationUpdate,
    LocationRead,
)

# Credential schemas
from src.schemas.credential import (
    CredentialBase,
    CredentialCreate,
    CredentialUpdate,
    CredentialRead,
)

# ToolIssued schemas (singular naming to match router imports)
from src.schemas.tools import (
    ToolIssuedBase,
    ToolIssuedCreate,
    ToolIssuedUpdate,
    ToolIssuedRead,
)

# Auth schemas
from src.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserRead,
    UserReadWithRoles,
)
from src.schemas.role import RoleBase, RoleCreate, RoleUpdate, RoleRead
from src.schemas.user_role import UserRoleBase, UserRoleCreate, UserRoleRead
from src.schemas.refresh_token import RefreshTokenCreate, RefreshTokenRead
from src.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserRegistrationRequest,
    CurrentUserResponse,
)

# Grant schemas
from src.schemas.grant import (
    GrantBase,
    GrantCreate,
    GrantUpdate,
    GrantRead,
    GrantSummary,
    GrantMetrics,
)
from src.schemas.grant_enrollment import (
    GrantEnrollmentBase,
    GrantEnrollmentCreate,
    GrantEnrollmentUpdate,
    GrantEnrollmentRead,
    GrantEnrollmentWithStudent,
    GrantEnrollmentWithGrant,
    RecordOutcome,
)

__all__ = [
    "StudentBase",
    "StudentCreate",
    "StudentUpdate",
    "StudentRead",
    "InstructorBase",
    "InstructorCreate",
    "InstructorUpdate",
    "InstructorRead",
    "CohortBase",
    "CohortCreate",
    "CohortUpdate",
    "CohortRead",
    "LocationBase",
    "LocationCreate",
    "LocationUpdate",
    "LocationRead",
    "CredentialBase",
    "CredentialCreate",
    "CredentialUpdate",
    "CredentialRead",
    "ToolIssuedBase",
    "ToolIssuedCreate",
    "ToolIssuedUpdate",
    "ToolIssuedRead",
    # Auth
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserRead",
    "UserReadWithRoles",
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleRead",
    "UserRoleBase",
    "UserRoleCreate",
    "UserRoleRead",
    "RefreshTokenCreate",
    "RefreshTokenRead",
    # Auth operations
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "UserRegistrationRequest",
    "CurrentUserResponse",
    # Grant schemas
    "GrantBase",
    "GrantCreate",
    "GrantUpdate",
    "GrantRead",
    "GrantSummary",
    "GrantMetrics",
    "GrantEnrollmentBase",
    "GrantEnrollmentCreate",
    "GrantEnrollmentUpdate",
    "GrantEnrollmentRead",
    "GrantEnrollmentWithStudent",
    "GrantEnrollmentWithGrant",
    "RecordOutcome",
]
