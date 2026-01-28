"""Pydantic schemas for UserRole model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserRoleBase(BaseModel):
    """Base schema for UserRole."""

    user_id: int
    role_id: int


class UserRoleCreate(UserRoleBase):
    """Schema for creating a UserRole."""

    assigned_by: Optional[str] = None
    expires_at: Optional[datetime] = None


class UserRoleRead(UserRoleBase):
    """Schema for reading a UserRole."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    assigned_by: Optional[str] = None
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
