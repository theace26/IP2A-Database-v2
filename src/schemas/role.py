"""Pydantic schemas for Role model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    """Base schema for Role."""

    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Schema for creating a Role."""

    is_system_role: bool = False


class RoleUpdate(BaseModel):
    """Schema for updating a Role."""

    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class RoleRead(RoleBase):
    """Schema for reading a Role."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_system_role: bool
    created_at: datetime
    updated_at: datetime
