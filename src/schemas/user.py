"""Pydantic schemas for User model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

if TYPE_CHECKING:
    from src.schemas.role import RoleRead


class UserBase(BaseModel):
    """Base schema for User."""

    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a User."""

    password: str = Field(..., min_length=8, max_length=128)
    member_id: Optional[int] = None


class UserUpdate(BaseModel):
    """Schema for updating a User."""

    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    member_id: Optional[int] = None


class UserRead(UserBase):
    """Schema for reading a User."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    member_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    role_names: list[str] = []


class UserReadWithRoles(UserRead):
    """Schema for reading a User with full role details."""

    roles: list["RoleRead"] = []
