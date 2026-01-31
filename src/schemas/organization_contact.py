"""OrganizationContact schemas for API requests/responses."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class OrganizationContactBase(BaseModel):
    """Base organization contact fields."""

    organization_id: int
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    title: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    is_primary: bool = False
    notes: Optional[str] = Field(None, max_length=500)


class OrganizationContactCreate(OrganizationContactBase):
    """Schema for creating a new organization contact."""

    pass


class OrganizationContactUpdate(BaseModel):
    """Schema for updating an organization contact."""

    organization_id: Optional[int] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)


class OrganizationContactRead(OrganizationContactBase):
    """Schema for reading an organization contact."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
