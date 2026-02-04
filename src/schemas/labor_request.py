"""LaborRequest schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date, time
from decimal import Decimal

from src.db.enums import (
    LaborRequestStatus,
    BookClassification,
    BookRegion,
    NoCheckMarkReason,
    AgreementType,
    JobClass,
)


class LaborRequestBase(BaseModel):
    """Base labor request fields."""

    employer_id: int
    workers_requested: int = Field(default=1, ge=1)
    start_date: date
    start_time: Optional[time] = None
    worksite_name: Optional[str] = Field(None, max_length=200)
    worksite_address: Optional[str] = Field(None, max_length=300)
    city: Optional[str] = Field(None, max_length=100)
    state: str = Field(default="WA", max_length=2)


class LaborRequestCreate(LaborRequestBase):
    """Schema for creating a labor request."""

    book_id: Optional[int] = None
    contract_code: Optional[str] = Field(None, max_length=30)
    job_class: Optional[JobClass] = None
    classification: Optional[BookClassification] = None
    region: Optional[BookRegion] = None
    estimated_duration_days: Optional[int] = Field(None, ge=1)
    is_short_call: bool = False
    short_call_days: Optional[int] = Field(None, ge=1, le=10)
    is_foreperson_by_name: bool = False
    foreperson_member_id: Optional[int] = None
    generates_check_mark: bool = True
    no_check_mark_reason: Optional[NoCheckMarkReason] = None
    agreement_type: Optional[AgreementType] = None
    wage_rate: Optional[Decimal] = Field(None, ge=0)
    requirements: Optional[str] = None
    comments: Optional[str] = None
    allows_online_bidding: bool = True
    report_to_address: Optional[str] = Field(None, max_length=300)


class LaborRequestUpdate(BaseModel):
    """Schema for updating a labor request."""

    workers_requested: Optional[int] = Field(None, ge=1)
    start_date: Optional[date] = None
    start_time: Optional[time] = None
    worksite_name: Optional[str] = Field(None, max_length=200)
    worksite_address: Optional[str] = Field(None, max_length=300)
    city: Optional[str] = Field(None, max_length=100)
    estimated_duration_days: Optional[int] = Field(None, ge=1)
    is_short_call: Optional[bool] = None
    short_call_days: Optional[int] = Field(None, ge=1, le=10)
    generates_check_mark: Optional[bool] = None
    no_check_mark_reason: Optional[NoCheckMarkReason] = None
    wage_rate: Optional[Decimal] = Field(None, ge=0)
    requirements: Optional[str] = None
    comments: Optional[str] = None
    status: Optional[LaborRequestStatus] = None
    allows_online_bidding: Optional[bool] = None


class LaborRequestRead(LaborRequestBase):
    """Schema for reading a labor request."""

    id: int
    employer_name: Optional[str] = None
    book_id: Optional[int] = None
    contract_code: Optional[str] = None
    job_class: Optional[JobClass] = None
    classification: Optional[BookClassification] = None
    region: Optional[BookRegion] = None
    request_number: Optional[str] = None
    request_date: datetime
    workers_dispatched: int = 0
    estimated_duration_days: Optional[int] = None
    is_short_call: bool = False
    short_call_days: Optional[int] = None
    is_foreperson_by_name: bool = False
    foreperson_member_id: Optional[int] = None
    generates_check_mark: bool = True
    no_check_mark_reason: Optional[NoCheckMarkReason] = None
    agreement_type: Optional[AgreementType] = None
    wage_rate: Optional[Decimal] = None
    requirements: Optional[str] = None
    comments: Optional[str] = None
    status: LaborRequestStatus
    allows_online_bidding: bool = True
    bidding_opens_at: Optional[datetime] = None
    bidding_closes_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LaborRequestWithDetails(LaborRequestRead):
    """Labor request with computed fields."""

    workers_remaining: int = 0
    is_filled: bool = False
    is_bidding_open: bool = False
    bids_count: int = 0
    dispatches_count: int = 0
