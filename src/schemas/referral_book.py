"""ReferralBook schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, time

from src.db.enums import BookClassification, BookRegion


class ReferralBookBase(BaseModel):
    """Base referral book fields."""

    name: str = Field(..., max_length=100, description="Display name: 'Wire Seattle'")
    code: str = Field(..., max_length=30, description="Unique code: 'WIRE_SEA_1'")
    classification: BookClassification
    book_number: int = Field(default=1, ge=1, le=3)
    region: BookRegion
    referral_start_time: Optional[time] = None
    re_sign_days: int = Field(default=30, ge=1)
    max_check_marks: int = Field(default=2, ge=0)
    grace_period_days: Optional[int] = Field(None, ge=0)
    max_days_on_book: Optional[int] = Field(None, ge=1)
    is_active: bool = True
    internet_bidding_enabled: bool = True


class ReferralBookCreate(ReferralBookBase):
    """Schema for creating a new referral book."""

    pass


class ReferralBookUpdate(BaseModel):
    """Schema for updating a referral book."""

    name: Optional[str] = Field(None, max_length=100)
    referral_start_time: Optional[time] = None
    re_sign_days: Optional[int] = Field(None, ge=1)
    max_check_marks: Optional[int] = Field(None, ge=0)
    grace_period_days: Optional[int] = Field(None, ge=0)
    max_days_on_book: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    internet_bidding_enabled: Optional[bool] = None


class ReferralBookRead(ReferralBookBase):
    """Schema for reading a referral book."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReferralBookStats(BaseModel):
    """Statistics for a referral book."""

    book_id: int
    book_name: str
    book_code: str
    total_registered: int = 0
    active_count: int = 0
    dispatched_count: int = 0
    with_check_mark: int = 0
    without_check_mark: int = 0
    exempt_count: int = 0


class ReferralBookSummary(ReferralBookRead):
    """Referral book with registration counts."""

    active_registrations: int = 0
    total_registrations: int = 0
