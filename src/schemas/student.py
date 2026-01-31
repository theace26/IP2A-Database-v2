"""Student schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date

from src.db.enums import StudentStatus


class StudentBase(BaseModel):
    """Base student fields."""

    member_id: int
    student_number: str = Field(..., max_length=20)
    status: StudentStatus = StudentStatus.APPLICANT
    application_date: date
    enrollment_date: Optional[date] = None
    expected_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    cohort: Optional[str] = Field(None, max_length=50)
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class StudentCreate(StudentBase):
    """Schema for creating a new student."""

    pass


class StudentUpdate(BaseModel):
    """Schema for updating a student."""

    member_id: Optional[int] = None
    student_number: Optional[str] = Field(None, max_length=20)
    status: Optional[StudentStatus] = None
    application_date: Optional[date] = None
    enrollment_date: Optional[date] = None
    expected_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    cohort: Optional[str] = Field(None, max_length=50)
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class StudentRead(StudentBase):
    """Schema for reading a student."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StudentReadWithDetails(StudentRead):
    """Schema for reading a student with computed details."""

    enrollment_count: int = 0
    certification_count: int = 0
    attendance_rate: float = 0.0

    class Config:
        from_attributes = True
