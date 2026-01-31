"""Pydantic schemas for dues periods."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class DuesPeriodBase(BaseModel):
    """Base schema for dues period."""
    period_year: int = Field(..., ge=2000, le=2100)
    period_month: int = Field(..., ge=1, le=12)
    due_date: date
    grace_period_end: date
    notes: Optional[str] = None


class DuesPeriodCreate(DuesPeriodBase):
    """Schema for creating a dues period."""
    pass


class DuesPeriodUpdate(BaseModel):
    """Schema for updating a dues period."""
    due_date: Optional[date] = None
    grace_period_end: Optional[date] = None
    notes: Optional[str] = None


class DuesPeriodRead(DuesPeriodBase):
    """Schema for reading a dues period."""
    id: int
    is_closed: bool
    closed_at: Optional[datetime] = None
    period_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DuesPeriodClose(BaseModel):
    """Schema for closing a period."""
    closed_by_id: Optional[int] = None
    notes: Optional[str] = None
