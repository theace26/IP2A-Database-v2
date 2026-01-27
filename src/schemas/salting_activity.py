"""SALTing activity schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date

from src.db.enums import SALTingActivityType, SALTingOutcome


class SALTingActivityBase(BaseModel):
    """Base SALTing activity fields."""

    member_id: int
    organization_id: int
    activity_type: SALTingActivityType
    activity_date: date
    outcome: Optional[SALTingOutcome] = None
    location: Optional[str] = Field(None, max_length=255)
    workers_contacted: Optional[int] = 0
    cards_signed: Optional[int] = 0
    description: Optional[str] = None
    notes: Optional[str] = None


class SALTingActivityCreate(SALTingActivityBase):
    """Schema for creating a SALTing activity."""

    pass


class SALTingActivityUpdate(BaseModel):
    """Schema for updating a SALTing activity."""

    member_id: Optional[int] = None
    organization_id: Optional[int] = None
    activity_type: Optional[SALTingActivityType] = None
    activity_date: Optional[date] = None
    outcome: Optional[SALTingOutcome] = None
    location: Optional[str] = Field(None, max_length=255)
    workers_contacted: Optional[int] = None
    cards_signed: Optional[int] = None
    description: Optional[str] = None
    notes: Optional[str] = None


class SALTingActivityRead(SALTingActivityBase):
    """Schema for reading a SALTing activity."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
