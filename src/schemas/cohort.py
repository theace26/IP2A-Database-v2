from pydantic import BaseModel
from typing import List, Optional
from datetime import date


# --------------------------------------------------------------------
# Base Schema (shared fields)
# --------------------------------------------------------------------
class CohortBase(BaseModel):
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location_id: Optional[int] = None  # FK → Location


# --------------------------------------------------------------------
# Create Schema (POST)
# --------------------------------------------------------------------
class CohortCreate(CohortBase):
    """Used when creating a new cohort."""

    instructor_ids: List[int] = []  # M2M
    student_ids: List[int] = []  # optional list on creation


# --------------------------------------------------------------------
# Update Schema (PUT/PATCH)
# --------------------------------------------------------------------
class CohortUpdate(BaseModel):
    """Used when updating an existing cohort."""

    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location_id: Optional[int] = None


# --------------------------------------------------------------------
# Read Schema (GET responses)
# --------------------------------------------------------------------
class CohortRead(CohortBase):
    """Returned when reading a cohort."""

    id: int

    class Config:
        from_attributes = True
