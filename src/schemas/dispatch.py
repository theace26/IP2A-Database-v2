"""Dispatch schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date, time
from decimal import Decimal

from src.db.enums import (
    DispatchStatus,
    DispatchMethod,
    DispatchType,
    TermReason,
    JobClass,
)


class DispatchBase(BaseModel):
    """Base dispatch fields."""

    labor_request_id: int
    member_id: int
    employer_id: int
    start_date: date


class DispatchCreate(DispatchBase):
    """Schema for creating a dispatch."""

    registration_id: Optional[int] = None
    bid_id: Optional[int] = None
    dispatch_method: DispatchMethod = DispatchMethod.MORNING_REFERRAL
    dispatch_type: DispatchType = DispatchType.NORMAL
    job_class: Optional[JobClass] = None
    book_code: Optional[str] = Field(None, max_length=30)
    contract_code: Optional[str] = Field(None, max_length=30)
    worksite: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    start_time: Optional[time] = None
    end_date: Optional[date] = None
    start_rate: Optional[Decimal] = Field(None, ge=0)
    is_short_call: bool = False
    restore_to_book: bool = False
    notes: Optional[str] = None


class DispatchUpdate(BaseModel):
    """Schema for updating a dispatch."""

    dispatch_status: Optional[DispatchStatus] = None
    checked_in: Optional[bool] = None
    term_date: Optional[date] = None
    term_reason: Optional[TermReason] = None
    term_comment: Optional[str] = Field(None, max_length=200)
    days_worked: Optional[int] = Field(None, ge=0)
    hours_worked: Optional[Decimal] = Field(None, ge=0)
    term_rate: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class DispatchCheckIn(BaseModel):
    """Schema for checking in a dispatch."""

    checked_in: bool = True
    notes: Optional[str] = None


class DispatchTerminate(BaseModel):
    """Schema for terminating a dispatch."""

    term_date: date
    term_reason: TermReason
    term_comment: Optional[str] = Field(None, max_length=200)
    days_worked: Optional[int] = Field(None, ge=0)
    hours_worked: Optional[Decimal] = Field(None, ge=0)
    term_rate: Optional[Decimal] = Field(None, ge=0)


class DispatchRead(DispatchBase):
    """Schema for reading a dispatch."""

    id: int
    registration_id: Optional[int] = None
    bid_id: Optional[int] = None
    dispatch_date: datetime
    dispatch_method: DispatchMethod
    dispatch_type: DispatchType
    dispatched_by_id: int
    job_class: Optional[JobClass] = None
    book_code: Optional[str] = None
    contract_code: Optional[str] = None
    worksite: Optional[str] = None
    worksite_code: Optional[str] = None
    city: Optional[str] = None
    start_time: Optional[time] = None
    end_date: Optional[date] = None
    start_rate: Optional[Decimal] = None
    term_rate: Optional[Decimal] = None
    dispatch_status: DispatchStatus
    check_in_deadline: Optional[datetime] = None
    checked_in: bool = False
    checked_in_at: Optional[datetime] = None
    is_short_call: bool = False
    restore_to_book: bool = False
    restored_at: Optional[datetime] = None
    term_date: Optional[date] = None
    term_reason: Optional[TermReason] = None
    term_comment: Optional[str] = None
    days_worked: Optional[int] = None
    hours_worked: Optional[Decimal] = None
    employment_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DispatchWithDetails(DispatchRead):
    """Dispatch with related entity details."""

    member_name: Optional[str] = None
    member_number: Optional[str] = None
    employer_name: Optional[str] = None
    dispatched_by_name: Optional[str] = None
    is_active: bool = False
    is_completed: bool = False
