from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date


# ------------------------------------------------------------
# Base Schema (shared fields)
# ------------------------------------------------------------
class StudentBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    shoe_size: Optional[str] = None
    demographic_info: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    cohort_id: Optional[int] = None  # foreign key to Cohort


# ------------------------------------------------------------
# Create Schema (POST)
# ------------------------------------------------------------
class StudentCreate(StudentBase):
    """Used when creating a new student."""
    pass


# ------------------------------------------------------------
# Update Schema (PATCH)
# ------------------------------------------------------------
class StudentUpdate(BaseModel):
    """Fields allowed to change on update."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    shoe_size: Optional[str] = None
    demographic_info: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    cohort_id: Optional[int] = None


# ------------------------------------------------------------
# Response Schema (GET)
# ------------------------------------------------------------
class StudentRead(StudentBase):
    id: int

    # You may later replace these with nested objects
    credential_ids: List[int] = []
    tools_issued_ids: List[int] = []
    jatc_application_ids: List[int] = []

    class Config:
        from_attributes = True
