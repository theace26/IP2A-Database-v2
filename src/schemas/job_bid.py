"""JobBid schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from src.db.enums import BidStatus


class JobBidBase(BaseModel):
    """Base job bid fields."""

    labor_request_id: int
    member_id: int


class JobBidCreate(JobBidBase):
    """Schema for creating a job bid."""

    registration_id: Optional[int] = None
    bid_method: str = Field(default="online", max_length=20)
    notes: Optional[str] = None


class JobBidUpdate(BaseModel):
    """Schema for updating a job bid."""

    bid_status: Optional[BidStatus] = None
    notes: Optional[str] = None


class JobBidProcess(BaseModel):
    """Schema for processing a job bid (accept/reject)."""

    bid_status: BidStatus
    rejection_reason: Optional[str] = Field(None, max_length=200)


class JobBidRead(JobBidBase):
    """Schema for reading a job bid."""

    id: int
    registration_id: Optional[int] = None
    bid_submitted_at: datetime
    bid_method: Optional[str] = None
    queue_position_at_bid: Optional[int] = None
    bid_status: BidStatus
    processed_at: Optional[datetime] = None
    was_dispatched: bool = False
    dispatch_id: Optional[int] = None
    rejected_by_member: bool = False
    rejection_reason: Optional[str] = None
    rejection_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobBidWithDetails(JobBidRead):
    """Job bid with related entity details."""

    member_name: Optional[str] = None
    member_number: Optional[str] = None
    employer_name: Optional[str] = None
    job_class: Optional[str] = None
