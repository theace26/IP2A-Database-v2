"""Pydantic schemas for dues adjustments."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.db.enums import DuesAdjustmentType, AdjustmentStatus


class DuesAdjustmentBase(BaseModel):
    """Base schema for dues adjustment."""
    member_id: int
    payment_id: Optional[int] = None
    adjustment_type: DuesAdjustmentType
    amount: Decimal = Field(..., decimal_places=2)
    reason: str = Field(..., min_length=10)


class DuesAdjustmentCreate(DuesAdjustmentBase):
    """Schema for creating an adjustment."""
    pass


class DuesAdjustmentApprove(BaseModel):
    """Schema for approving/denying adjustment."""
    approved_by_id: Optional[int] = None
    approved: bool
    notes: Optional[str] = None


class DuesAdjustmentRead(DuesAdjustmentBase):
    """Schema for reading an adjustment."""
    id: int
    status: AdjustmentStatus
    requested_by_id: Optional[int]
    approved_by_id: Optional[int]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
