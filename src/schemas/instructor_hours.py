from pydantic import BaseModel
from datetime import date
from typing import Optional


# ------------------------------------------------------------
# Base Schema (shared fields)
# ------------------------------------------------------------
class InstructorHoursBase(BaseModel):
    instructor_id: int  # FK → Instructor
    cohort_id: Optional[int] = None  # FK → Cohort
    location_id: Optional[int] = None  # FK → Location
    date: date
    hours: float
    notes: Optional[str] = None


# ------------------------------------------------------------
# Create Schema (POST)
# ------------------------------------------------------------
class InstructorHoursCreate(InstructorHoursBase):
    """Used when logging new instructor hours."""

    pass


# ------------------------------------------------------------
# Update Schema (PATCH)
# ------------------------------------------------------------
class InstructorHoursUpdate(BaseModel):
    """Allows partial updates to instructor hour logs."""

    instructor_id: Optional[int] = None
    cohort_id: Optional[int] = None
    location_id: Optional[int] = None
    date: Optional[date] = None
    hours: Optional[float] = None
    notes: Optional[str] = None


# ------------------------------------------------------------
# Response Schema (GET)
# ------------------------------------------------------------
class InstructorHoursRead(InstructorHoursBase):
    id: int

    class Config:
        from_attributes = True  # Pydantic v2 equivalent of orm_mode
