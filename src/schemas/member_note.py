"""Pydantic schemas for member notes."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MemberNoteBase(BaseModel):
    """Base schema for member note."""
    note_text: str = Field(..., min_length=1, max_length=10000)
    visibility: str = Field(default="staff_only")
    category: Optional[str] = Field(default=None, max_length=50)


class MemberNoteCreate(MemberNoteBase):
    """Schema for creating a member note."""
    member_id: int


class MemberNoteUpdate(BaseModel):
    """Schema for updating a member note."""
    note_text: Optional[str] = Field(None, min_length=1, max_length=10000)
    visibility: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)


class MemberNoteRead(MemberNoteBase):
    """Schema for reading a member note."""
    id: int
    member_id: int
    created_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    # Include creator info
    created_by_name: Optional[str] = None

    class Config:
        from_attributes = True


class MemberNoteList(BaseModel):
    """Schema for listing member notes."""
    items: list[MemberNoteRead]
    total: int
