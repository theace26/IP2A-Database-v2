"""Class session schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date, time


class ClassSessionBase(BaseModel):
    """Base class session fields."""

    course_id: int
    session_date: date
    start_time: time
    end_time: time
    location: Optional[str] = Field(None, max_length=200)
    room: Optional[str] = Field(None, max_length=50)
    instructor_name: Optional[str] = Field(None, max_length=200)
    topic: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None
    is_cancelled: bool = False
    cancellation_reason: Optional[str] = Field(None, max_length=200)


class ClassSessionCreate(ClassSessionBase):
    """Schema for creating a new class session."""

    pass


class ClassSessionUpdate(BaseModel):
    """Schema for updating a class session."""

    course_id: Optional[int] = None
    session_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = Field(None, max_length=200)
    room: Optional[str] = Field(None, max_length=50)
    instructor_name: Optional[str] = Field(None, max_length=200)
    topic: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None
    is_cancelled: Optional[bool] = None
    cancellation_reason: Optional[str] = Field(None, max_length=200)


class ClassSessionRead(ClassSessionBase):
    """Schema for reading a class session."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
