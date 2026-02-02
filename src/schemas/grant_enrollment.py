"""Pydantic schemas for grant enrollments."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.db.enums import GrantEnrollmentStatus, GrantOutcome


class GrantEnrollmentBase(BaseModel):
    """Base schema for grant enrollment."""
    grant_id: int
    student_id: int
    enrollment_date: date
    notes: Optional[str] = None


class GrantEnrollmentCreate(GrantEnrollmentBase):
    """Schema for creating a grant enrollment."""
    status: GrantEnrollmentStatus = GrantEnrollmentStatus.ENROLLED


class GrantEnrollmentUpdate(BaseModel):
    """Schema for updating a grant enrollment."""
    status: Optional[GrantEnrollmentStatus] = None
    completion_date: Optional[date] = None
    outcome: Optional[GrantOutcome] = None
    outcome_date: Optional[date] = None
    placement_employer: Optional[str] = Field(None, max_length=200)
    placement_date: Optional[date] = None
    placement_wage: Optional[str] = Field(None, max_length=50)
    placement_job_title: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class GrantEnrollmentRead(GrantEnrollmentBase):
    """Schema for reading a grant enrollment."""
    id: int
    status: GrantEnrollmentStatus
    completion_date: Optional[date] = None
    outcome: Optional[GrantOutcome] = None
    outcome_date: Optional[date] = None
    placement_employer: Optional[str] = None
    placement_date: Optional[date] = None
    placement_wage: Optional[str] = None
    placement_job_title: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GrantEnrollmentWithStudent(GrantEnrollmentRead):
    """Enrollment with student details for list views."""
    student_name: str
    student_number: str

    class Config:
        from_attributes = True


class GrantEnrollmentWithGrant(GrantEnrollmentRead):
    """Enrollment with grant details for student views."""
    grant_name: str
    grant_number: Optional[str] = None

    class Config:
        from_attributes = True


class RecordOutcome(BaseModel):
    """Schema for recording an outcome."""
    outcome: GrantOutcome
    outcome_date: date
    placement_employer: Optional[str] = Field(None, max_length=200)
    placement_date: Optional[date] = None
    placement_wage: Optional[str] = Field(None, max_length=50)
    placement_job_title: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None
