"""Pydantic schemas for dues rates."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.db.enums import MemberClassification


class DuesRateBase(BaseModel):
    """Base schema for dues rate."""
    classification: MemberClassification
    monthly_amount: Decimal = Field(..., ge=0, decimal_places=2)
    effective_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None


class DuesRateCreate(DuesRateBase):
    """Schema for creating a dues rate."""
    pass


class DuesRateUpdate(BaseModel):
    """Schema for updating a dues rate."""
    monthly_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    end_date: Optional[date] = None
    description: Optional[str] = None


class DuesRateRead(DuesRateBase):
    """Schema for reading a dues rate."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
