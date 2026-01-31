"""Benevolence application schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

from src.db.enums import BenevolenceReason, BenevolenceStatus


class BenevolenceApplicationBase(BaseModel):
    """Base benevolence application fields."""

    member_id: int
    application_date: date
    reason: BenevolenceReason
    description: str
    amount_requested: Decimal = Field(..., decimal_places=2)
    status: BenevolenceStatus = BenevolenceStatus.DRAFT
    approved_amount: Optional[Decimal] = Field(None, decimal_places=2)
    payment_date: Optional[date] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class BenevolenceApplicationCreate(BenevolenceApplicationBase):
    """Schema for creating a benevolence application."""

    pass


class BenevolenceApplicationUpdate(BaseModel):
    """Schema for updating a benevolence application."""

    member_id: Optional[int] = None
    application_date: Optional[date] = None
    reason: Optional[BenevolenceReason] = None
    description: Optional[str] = None
    amount_requested: Optional[Decimal] = Field(None, decimal_places=2)
    status: Optional[BenevolenceStatus] = None
    approved_amount: Optional[Decimal] = Field(None, decimal_places=2)
    payment_date: Optional[date] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class BenevolenceApplicationRead(BenevolenceApplicationBase):
    """Schema for reading a benevolence application."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
