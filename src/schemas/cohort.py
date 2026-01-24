from pydantic import BaseModel
from typing import List, Optional
from datetime import date


# ------------------------------------------------------------
# Base Schema (shared fields)
# ------------------------------------------------------------
class CohortBase(BaseModel):
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location_id: Optional[int] = None  # FK → Location


# ------------------------------------------------------------
# Create Schema (POST)
# ------------------------------------------------------------
class CohortCreate(CohortBase):
    """Used when creating a new cohort."""

    instructor_ids: List[int] = []  # M2M
    student_ids: List[int] = []  # optional list on creation


# ------------------------------------------------------------
# Update Schema (PATCH)
# ------------------------------------------------------------
class CohortUpdate(BaseModel):
    """Allows partial updates to a cohort."""

    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location_id: Optional[int] = None

    # Relationship updates
    instructor_ids: Optional[List[int]] = None
    student_ids: Optional[List[int]] = None


# ------------------------------------------------------------
# Read Schema (GET)
# ------------------------------------------------------------
class CohortRead(CohortBase):
    id: int
    instructor_ids: List[int] = []
    student_ids: List[int] = []

    class Config:
        from_attributes = True
