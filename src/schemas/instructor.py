from pydantic import BaseModel, EmailStr
from typing import List, Optional


# ---------------------
# Base Schema (shared)
# ---------------------
class InstructorBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


# ---------------------
# Create Schema (POST)
# ---------------------
class InstructorCreate(InstructorBase):
    """Fields required when creating a new instructor."""

    pass


# ---------------------
# Update Schema (PATCH)
# ---------------------
class InstructorUpdate(BaseModel):
    """Fields allowed during partial update."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None


# ---------------------
# Response Schema (GET)
# ---------------------
class InstructorRead(InstructorBase):
    id: int
    cohort_ids: List[int] = []

    class Config:
        from_attributes = True  # replaces orm_mode=True in Pydantic v2
