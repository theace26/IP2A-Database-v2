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
]
