"""BookRegistration schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

from src.db.enums import (
    RegistrationStatus,
    ExemptReason,
    RolloffReason,
)


class BookRegistrationBase(BaseModel):
    """Base book registration fields."""

    member_id: int
    book_id: int
    registration_number: Decimal = Field(..., decimal_places=2)
    registration_method: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class BookRegistrationCreate(BaseModel):
    """Schema for creating a new book registration."""

    member_id: int
    book_id: int
    registration_method: Optional[str] = Field("in_person", max_length=20)
    notes: Optional[str] = None


class BookRegistrationUpdate(BaseModel):
    """Schema for updating a book registration."""

    status: Optional[RegistrationStatus] = None
    is_exempt: Optional[bool] = None
    exempt_reason: Optional[ExemptReason] = None
    exempt_start_date: Optional[date] = None
    exempt_end_date: Optional[date] = None
    notes: Optional[str] = None


class BookRegistrationRead(BookRegistrationBase):
    """Schema for reading a book registration."""

    id: int
    status: RegistrationStatus
    registration_date: datetime

    # Re-sign tracking
    last_re_sign_date: Optional[datetime] = None
    re_sign_deadline: Optional[datetime] = None

    # Check marks
    check_marks: int = 0
    consecutive_missed_check_marks: int = 0
    has_check_mark: bool = True
    last_check_mark_date: Optional[date] = None
    last_check_mark_at: Optional[datetime] = None

    # Short call
    short_call_restorations: int = 0

    # Exempt status
    is_exempt: bool = False
    exempt_reason: Optional[ExemptReason] = None
    exempt_start_date: Optional[date] = None
    exempt_end_date: Optional[date] = None

    # Rolloff
    roll_off_date: Optional[datetime] = None
    roll_off_reason: Optional[RolloffReason] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BookRegistrationWithMember(BookRegistrationRead):
    """Registration with embedded member info."""

    member_name: Optional[str] = None
    member_number: Optional[str] = None
    book_name: Optional[str] = None
    book_code: Optional[str] = None


class QueuePosition(BaseModel):
    """Member's position in the book queue."""

    registration_id: int
    member_id: int
    member_name: str
    member_number: str
    registration_number: Decimal
    position: int
    status: RegistrationStatus
    check_marks: int
    is_exempt: bool
    days_on_book: int


class ReSignRequest(BaseModel):
    """Request to re-sign a registration."""

    registration_id: int
    notes: Optional[str] = None


class ExemptRequest(BaseModel):
    """Request to grant exempt status."""

    registration_id: int
    reason: ExemptReason
    end_date: Optional[date] = None
    notes: Optional[str] = None


class RolloffRequest(BaseModel):
    """Request to roll off a registration."""

    registration_id: int
    reason: RolloffReason
    notes: Optional[str] = None
