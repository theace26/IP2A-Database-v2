"""Pydantic schemas for dues payments."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.db.enums import DuesPaymentMethod, DuesPaymentStatus


class DuesPaymentBase(BaseModel):
    """Base schema for dues payment."""
    member_id: int
    period_id: int
    amount_due: Decimal = Field(..., ge=0, decimal_places=2)


class DuesPaymentCreate(DuesPaymentBase):
    """Schema for creating a dues payment record."""
    pass


class DuesPaymentRecord(BaseModel):
    """Schema for recording a payment."""
    amount_paid: Decimal = Field(..., gt=0, decimal_places=2)
    payment_date: date
    payment_method: DuesPaymentMethod
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class DuesPaymentUpdate(BaseModel):
    """Schema for updating a payment."""
    amount_paid: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    payment_date: Optional[date] = None
    payment_method: Optional[DuesPaymentMethod] = None
    reference_number: Optional[str] = None
    status: Optional[DuesPaymentStatus] = None
    notes: Optional[str] = None


class DuesPaymentRead(DuesPaymentBase):
    """Schema for reading a payment."""
    id: int
    amount_paid: Decimal
    payment_date: Optional[date]
    payment_method: Optional[DuesPaymentMethod]
    status: DuesPaymentStatus
    reference_number: Optional[str]
    receipt_number: Optional[str]
    balance_due: Decimal
    is_paid_in_full: bool
    processed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DuesPaymentWithMember(DuesPaymentRead):
    """Payment with member details."""
    member_name: str
    member_number: str
    period_name: str


class MemberDuesSummary(BaseModel):
    """Summary of member's dues status."""
    member_id: int
    member_name: str
    classification: str
    total_due: Decimal
    total_paid: Decimal
    balance: Decimal
    periods_overdue: int
    last_payment_date: Optional[date]
