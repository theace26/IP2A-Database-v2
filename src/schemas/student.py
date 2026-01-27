"""
Student Pydantic schemas - aligned with src/models/student.py

Model fields:
- id, first_name, last_name, email, phone, birthdate, address
- cohort_id, profile_photo_path
- relationships: cohort, tools_issued, credentials, jatc_applications
"""

from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date


# ------------------------------------------------------------
# Base Schema (shared fields - matches model exactly)
# ------------------------------------------------------------
class StudentBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None  # Model uses 'phone', not 'phone_number'
    birthdate: Optional[date] = None  # Model uses 'birthdate', not 'date_of_birth'
    address: Optional[str] = None
    cohort_id: Optional[int] = None
    profile_photo_path: Optional[str] = None


# ------------------------------------------------------------
# Create Schema (POST)
# ------------------------------------------------------------
class StudentCreate(StudentBase):
    """Used when creating a new student."""

    pass


# ------------------------------------------------------------
# Update Schema (PATCH) - all fields optional
# ------------------------------------------------------------
class StudentUpdate(BaseModel):
    """Fields allowed to change on update."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birthdate: Optional[date] = None
    address: Optional[str] = None
    cohort_id: Optional[int] = None
    profile_photo_path: Optional[str] = None


# ------------------------------------------------------------
# Response Schema (GET)
# ------------------------------------------------------------
class StudentRead(StudentBase):
    id: int

    # Relationship IDs for reference (can be replaced with nested objects later)
    credential_ids: List[int] = []
    tools_issued_ids: List[int] = []
    jatc_application_ids: List[int] = []

    class Config:
        from_attributes = True
