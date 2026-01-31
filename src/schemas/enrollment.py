"""Enrollment schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date

from src.db.enums import CourseEnrollmentStatus


class EnrollmentBase(BaseModel):
    """Base enrollment fields."""

    student_id: int
    course_id: int
    cohort: str = Field(..., max_length=50)
    enrollment_date: date
    completion_date: Optional[date] = None
    status: CourseEnrollmentStatus = CourseEnrollmentStatus.ENROLLED
    final_grade: Optional[float] = None
    letter_grade: Optional[str] = Field(None, max_length=2)
    notes: Optional[str] = None


class EnrollmentCreate(EnrollmentBase):
    """Schema for creating a new enrollment."""

    pass


class EnrollmentUpdate(BaseModel):
    """Schema for updating an enrollment."""

    student_id: Optional[int] = None
    course_id: Optional[int] = None
    cohort: Optional[str] = Field(None, max_length=50)
    enrollment_date: Optional[date] = None
    completion_date: Optional[date] = None
    status: Optional[CourseEnrollmentStatus] = None
    final_grade: Optional[float] = None
    letter_grade: Optional[str] = Field(None, max_length=2)
    notes: Optional[str] = None


class EnrollmentRead(EnrollmentBase):
    """Schema for reading an enrollment."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
