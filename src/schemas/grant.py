"""Pydantic schemas for grants."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field

from src.db.enums import GrantStatus


class GrantBase(BaseModel):
    """Base schema for grant."""
    name: str = Field(..., max_length=255)
    grant_number: Optional[str] = Field(None, max_length=100)
    funding_source: Optional[str] = Field(None, max_length=255)
    total_amount: Decimal = Field(..., ge=0)
    start_date: date
    end_date: Optional[date] = None
    reporting_frequency: Optional[str] = Field(None, max_length=50)
    next_report_due: Optional[date] = None
    notes: Optional[str] = None
    target_enrollment: Optional[int] = Field(None, ge=0)
    target_completion: Optional[int] = Field(None, ge=0)
    target_placement: Optional[int] = Field(None, ge=0)


class GrantCreate(GrantBase):
    """Schema for creating a grant."""
    status: GrantStatus = GrantStatus.PENDING
    is_active: bool = True
    allowable_categories: Optional[List[str]] = None


class GrantUpdate(BaseModel):
    """Schema for updating a grant."""
    name: Optional[str] = Field(None, max_length=255)
    grant_number: Optional[str] = Field(None, max_length=100)
    funding_source: Optional[str] = Field(None, max_length=255)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reporting_frequency: Optional[str] = Field(None, max_length=50)
    next_report_due: Optional[date] = None
    notes: Optional[str] = None
    status: Optional[GrantStatus] = None
    is_active: Optional[bool] = None
    target_enrollment: Optional[int] = Field(None, ge=0)
    target_completion: Optional[int] = Field(None, ge=0)
    target_placement: Optional[int] = Field(None, ge=0)
    allowable_categories: Optional[List[str]] = None


class GrantRead(GrantBase):
    """Schema for reading a grant."""
    id: int
    status: GrantStatus
    is_active: bool
    spent_amount: Optional[Decimal] = Decimal("0")
    allowable_categories: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GrantSummary(BaseModel):
    """Summary schema for grant list views."""
    id: int
    name: str
    grant_number: Optional[str] = None
    funding_source: Optional[str] = None
    status: GrantStatus
    total_amount: Decimal
    spent_amount: Optional[Decimal] = Decimal("0")
    start_date: date
    end_date: Optional[date] = None
    target_enrollment: Optional[int] = None
    current_enrollment: int = 0  # Calculated field
    is_active: bool

    class Config:
        from_attributes = True


class GrantMetrics(BaseModel):
    """Schema for grant metrics/statistics."""
    grant_id: int
    grant_name: str
    funder: Optional[str] = None

    # Enrollment metrics
    total_enrolled: int = 0
    currently_active: int = 0
    completed: int = 0
    attrition: int = 0
    retention_rate: float = 0.0

    # Financial metrics
    total_budget: float = 0.0
    total_spent: float = 0.0
    remaining: float = 0.0
    utilization_rate: float = 0.0

    # Outcome metrics
    placement_count: int = 0
    total_with_outcomes: int = 0

    # Progress toward targets
    enrollment_progress: Optional[float] = None
    completion_progress: Optional[float] = None
    placement_progress: Optional[float] = None
