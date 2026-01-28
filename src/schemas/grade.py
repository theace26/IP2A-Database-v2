"""Grade schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date

from src.db.enums import GradeType


class GradeBase(BaseModel):
    """Base grade fields."""

    student_id: int
    course_id: int
    grade_type: GradeType
    name: str = Field(..., max_length=200)
    points_earned: float
    points_possible: float
    weight: float = 1.0
    grade_date: date
    feedback: Optional[str] = None
    graded_by: Optional[str] = Field(None, max_length=200)


class GradeCreate(GradeBase):
    """Schema for creating a new grade."""

    pass


class GradeUpdate(BaseModel):
    """Schema for updating a grade."""

    student_id: Optional[int] = None
    course_id: Optional[int] = None
    grade_type: Optional[GradeType] = None
    name: Optional[str] = Field(None, max_length=200)
    points_earned: Optional[float] = None
    points_possible: Optional[float] = None
    weight: Optional[float] = None
    grade_date: Optional[date] = None
    feedback: Optional[str] = None
    graded_by: Optional[str] = Field(None, max_length=200)


class GradeRead(GradeBase):
    """Schema for reading a grade."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
