"""Organization schemas for API requests/responses."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

from src.db.enums import OrganizationType, SaltingScore


class OrganizationBase(BaseModel):
    """Base organization fields."""

    name: str = Field(..., max_length=255)
    org_type: OrganizationType
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)
    salting_score: Optional[SaltingScore] = None
    salting_notes: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization."""

    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""

    name: Optional[str] = Field(None, max_length=255)
    org_type: Optional[OrganizationType] = None
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)
    salting_score: Optional[SaltingScore] = None
    salting_notes: Optional[str] = None


class OrganizationRead(OrganizationBase):
    """Schema for reading an organization."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
