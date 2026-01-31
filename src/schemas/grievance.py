"""Grievance schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

from src.db.enums import GrievanceStep, GrievanceStatus, GrievanceStepOutcome


class GrievanceBase(BaseModel):
    """Base grievance fields."""

    grievance_number: str = Field(..., max_length=20)
    member_id: int
    employer_id: int
    filed_date: date
    incident_date: Optional[date] = None
    contract_article: Optional[str] = Field(None, max_length=50)
    violation_description: str
    remedy_sought: Optional[str] = None
    current_step: GrievanceStep = GrievanceStep.STEP_1
    status: GrievanceStatus = GrievanceStatus.OPEN
    assigned_rep: Optional[str] = Field(None, max_length=100)
    resolution: Optional[str] = None
    resolution_date: Optional[date] = None
    settlement_amount: Optional[Decimal] = Field(None, decimal_places=2)
    notes: Optional[str] = None


class GrievanceCreate(GrievanceBase):
    """Schema for creating a grievance."""

    pass


class GrievanceUpdate(BaseModel):
    """Schema for updating a grievance."""

    grievance_number: Optional[str] = Field(None, max_length=20)
    member_id: Optional[int] = None
    employer_id: Optional[int] = None
    filed_date: Optional[date] = None
    incident_date: Optional[date] = None
    contract_article: Optional[str] = Field(None, max_length=50)
    violation_description: Optional[str] = None
    remedy_sought: Optional[str] = None
    current_step: Optional[GrievanceStep] = None
    status: Optional[GrievanceStatus] = None
    assigned_rep: Optional[str] = Field(None, max_length=100)
    resolution: Optional[str] = None
    resolution_date: Optional[date] = None
    settlement_amount: Optional[Decimal] = Field(None, decimal_places=2)
    notes: Optional[str] = None


class GrievanceRead(GrievanceBase):
    """Schema for reading a grievance."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Grievance Step Record Schemas ---


class GrievanceStepRecordBase(BaseModel):
    """Base grievance step record fields."""

    grievance_id: int
    step_number: int
    meeting_date: date
    union_attendees: Optional[str] = None
    employer_attendees: Optional[str] = None
    outcome: GrievanceStepOutcome
    notes: Optional[str] = None


class GrievanceStepRecordCreate(GrievanceStepRecordBase):
    """Schema for creating a grievance step record."""

    pass


class GrievanceStepRecordUpdate(BaseModel):
    """Schema for updating a grievance step record."""

    grievance_id: Optional[int] = None
    step_number: Optional[int] = None
    meeting_date: Optional[date] = None
    union_attendees: Optional[str] = None
    employer_attendees: Optional[str] = None
    outcome: Optional[GrievanceStepOutcome] = None
    notes: Optional[str] = None


class GrievanceStepRecordRead(GrievanceStepRecordBase):
    """Schema for reading a grievance step record."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
