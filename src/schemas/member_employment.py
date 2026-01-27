"""MemberEmployment schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


class MemberEmploymentBase(BaseModel):
    """Base member employment fields."""

    member_id: int
    organization_id: int
    start_date: date
    end_date: Optional[date] = None
    job_title: Optional[str] = Field(None, max_length=100)
    hourly_rate: Optional[Decimal] = None
    is_current: bool = True


class MemberEmploymentCreate(MemberEmploymentBase):
    """Schema for creating a new member employment record."""

    pass


class MemberEmploymentUpdate(BaseModel):
    """Schema for updating a member employment record."""

    member_id: Optional[int] = None
    organization_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    job_title: Optional[str] = Field(None, max_length=100)
    hourly_rate: Optional[Decimal] = None
    is_current: Optional[bool] = None


class MemberEmploymentRead(MemberEmploymentBase):
    """Schema for reading a member employment record."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
