"""Certification schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date

from src.db.enums import CertificationType, CertificationStatus


class CertificationBase(BaseModel):
    """Base certification fields."""

    student_id: int
    cert_type: CertificationType
    custom_name: Optional[str] = Field(None, max_length=200)
    status: CertificationStatus = CertificationStatus.PENDING
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None
    certificate_number: Optional[str] = Field(None, max_length=100)
    issuing_organization: Optional[str] = Field(None, max_length=200)
    verified_by: Optional[str] = Field(None, max_length=200)
    verification_date: Optional[date] = None
    notes: Optional[str] = None


class CertificationCreate(CertificationBase):
    """Schema for creating a new certification."""

    pass


class CertificationUpdate(BaseModel):
    """Schema for updating a certification."""

    student_id: Optional[int] = None
    cert_type: Optional[CertificationType] = None
    custom_name: Optional[str] = Field(None, max_length=200)
    status: Optional[CertificationStatus] = None
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None
    certificate_number: Optional[str] = Field(None, max_length=100)
    issuing_organization: Optional[str] = Field(None, max_length=200)
    verified_by: Optional[str] = Field(None, max_length=200)
    verification_date: Optional[date] = None
    notes: Optional[str] = None


class CertificationRead(CertificationBase):
    """Schema for reading a certification."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
