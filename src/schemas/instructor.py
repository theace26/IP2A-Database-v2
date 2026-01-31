"""
Instructor Pydantic schemas - aligned with src/models/instructor.py

Model fields:
- id, first_name, last_name, email, phone, bio, certification
- relationships: cohorts (m2m), hours_entries
"""

from pydantic import BaseModel, EmailStr
from typing import List, Optional


# ------------------------------------------------------------
# Base Schema (shared fields - matches model exactly)
# ------------------------------------------------------------
class InstructorBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    bio: Optional[str] = None
    certification: Optional[str] = None


# ------------------------------------------------------------
# Create Schema (POST)
# ------------------------------------------------------------
class InstructorCreate(InstructorBase):
    """Used when creating a new instructor."""

    pass


# ------------------------------------------------------------
# Update Schema (PATCH) - all fields optional
# ------------------------------------------------------------
class InstructorUpdate(BaseModel):
    """Fields allowed to change on update."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    certification: Optional[str] = None


# ------------------------------------------------------------
# Response Schema (GET)
# ------------------------------------------------------------
class InstructorRead(InstructorBase):
    id: int

    # Relationship IDs for reference
    cohort_ids: List[int] = []

    class Config:
        from_attributes = True
