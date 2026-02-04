"""RegistrationActivity schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from src.db.enums import RegistrationStatus, RegistrationAction


class RegistrationActivityBase(BaseModel):
    """Base registration activity fields."""

    action: RegistrationAction
    previous_status: Optional[RegistrationStatus] = None
    new_status: RegistrationStatus
    previous_position: Optional[int] = None
    new_position: Optional[int] = None
    details: Optional[str] = None
    reason: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None
    processor: Optional[str] = Field(None, max_length=100)


class RegistrationActivityCreate(RegistrationActivityBase):
    """Schema for creating a registration activity."""

    registration_id: Optional[int] = None
    member_id: int
    book_id: Optional[int] = None
    labor_request_id: Optional[int] = None
    dispatch_id: Optional[int] = None
    performed_by_id: int


class RegistrationActivityRead(RegistrationActivityBase):
    """Schema for reading a registration activity."""

    id: int
    registration_id: Optional[int] = None
    member_id: int
    book_id: Optional[int] = None
    labor_request_id: Optional[int] = None
    dispatch_id: Optional[int] = None
    performed_by_id: int
    activity_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class RegistrationActivityWithDetails(RegistrationActivityRead):
    """Activity with related entity details."""

    member_name: Optional[str] = None
    member_number: Optional[str] = None
    book_name: Optional[str] = None
    performed_by_name: Optional[str] = None
