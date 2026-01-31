"""Course schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from src.db.enums import CourseType


class CourseBase(BaseModel):
    """Base course fields."""

    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    course_type: CourseType = CourseType.CORE
    credits: float = 1.0
    hours: int = 40
    is_required: bool = True
    passing_grade: float = 70.0
    prerequisites: Optional[str] = Field(None, max_length=200)
    is_active: bool = True


class CourseCreate(CourseBase):
    """Schema for creating a new course."""

    pass


class CourseUpdate(BaseModel):
    """Schema for updating a course."""

    code: Optional[str] = Field(None, max_length=20)
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    course_type: Optional[CourseType] = None
    credits: Optional[float] = None
    hours: Optional[int] = None
    is_required: Optional[bool] = None
    passing_grade: Optional[float] = None
    prerequisites: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


class CourseRead(CourseBase):
    """Schema for reading a course."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
