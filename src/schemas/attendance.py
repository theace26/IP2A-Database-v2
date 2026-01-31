"""Attendance schemas for API requests/responses."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime, time

from src.db.enums import SessionAttendanceStatus


class AttendanceBase(BaseModel):
    """Base attendance fields."""

    student_id: int
    class_session_id: int
    status: SessionAttendanceStatus
    arrival_time: Optional[time] = None
    departure_time: Optional[time] = None
    notes: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    """Schema for creating a new attendance record."""

    pass


class AttendanceUpdate(BaseModel):
    """Schema for updating an attendance record."""

    student_id: Optional[int] = None
    class_session_id: Optional[int] = None
    status: Optional[SessionAttendanceStatus] = None
    arrival_time: Optional[time] = None
    departure_time: Optional[time] = None
    notes: Optional[str] = None


class AttendanceRead(AttendanceBase):
    """Schema for reading an attendance record."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
