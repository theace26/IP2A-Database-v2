"""Member schemas for API requests/responses."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, date

from src.db.enums import MemberStatus, MemberClassification


class MemberBase(BaseModel):
    """Base member fields."""

    member_number: str = Field(..., max_length=50)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    date_of_birth: Optional[date] = None
    hire_date: Optional[date] = None
    status: MemberStatus = MemberStatus.ACTIVE
    classification: MemberClassification
    general_notes: Optional[str] = None


class MemberCreate(MemberBase):
    """Schema for creating a new member."""

    pass


class MemberUpdate(BaseModel):
    """Schema for updating a member."""

    member_number: Optional[str] = Field(None, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    date_of_birth: Optional[date] = None
    hire_date: Optional[date] = None
    status: Optional[MemberStatus] = None
    classification: Optional[MemberClassification] = None
    general_notes: Optional[str] = None


class MemberRead(MemberBase):
    """Schema for reading a member."""

    id: int
    stripe_customer_id: Optional[str] = None  # Stripe payment integration
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
