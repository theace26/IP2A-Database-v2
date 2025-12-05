from pydantic import BaseModel
from typing import Optional
from datetime import date


# ------------------------------------------------------------
# Base Schema (shared fields)
# ------------------------------------------------------------
class JATCApplicationBase(BaseModel):
    application_date: Optional[date] = None
    application_status: Optional[str] = None
    interview_date: Optional[date] = None
    interview_score: Optional[int] = None
    aptitude_test_score: Optional[int] = None
    total_score: Optional[int] = None
    notes: Optional[str] = None
    student_id: int  # FK → Student


# ------------------------------------------------------------
# Create Schema (POST)
# ------------------------------------------------------------
class JATCApplicationCreate(JATCApplicationBase):
    """Used when creating a JATC application record."""
    pass


# ------------------------------------------------------------
# Update Schema (PATCH)
# ------------------------------------------------------------
class JATCApplicationUpdate(BaseModel):
    """Allows partial update of JATC application fields."""
    application_date: Optional[date] = None
    application_status: Optional[str] = None
    interview_date: Optional[date] = None
    interview_score: Optional[int] = None
    aptitude_test_score: Optional[int] = None
    total_score: Optional[int] = None
    notes: Optional[str] = None
    student_id: Optional[int] = None


# ------------------------------------------------------------
# Response Schema (GET)
# ------------------------------------------------------------
class JATCApplicationRead(JATCApplicationBase):
    id: int

    class Config:
        from_attributes = True
