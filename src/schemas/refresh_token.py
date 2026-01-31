"""Pydantic schemas for RefreshToken model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RefreshTokenCreate(BaseModel):
    """Schema for creating a RefreshToken (internal use)."""

    user_id: int
    token_hash: str
    expires_at: datetime
    device_info: Optional[str] = None
    ip_address: Optional[str] = None


class RefreshTokenRead(BaseModel):
    """Schema for reading a RefreshToken."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    expires_at: datetime
    is_revoked: bool
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
