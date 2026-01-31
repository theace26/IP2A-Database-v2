"""Benevolence review schemas for API requests/responses."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

from src.db.enums import BenevolenceReviewLevel, BenevolenceReviewDecision


class BenevolenceReviewBase(BaseModel):
    """Base benevolence review fields."""

    application_id: int
    reviewer_name: str
    review_level: BenevolenceReviewLevel
    decision: BenevolenceReviewDecision
    review_date: date
    comments: Optional[str] = None


class BenevolenceReviewCreate(BenevolenceReviewBase):
    """Schema for creating a benevolence review."""

    pass


class BenevolenceReviewUpdate(BaseModel):
    """Schema for updating a benevolence review."""

    application_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    review_level: Optional[BenevolenceReviewLevel] = None
    decision: Optional[BenevolenceReviewDecision] = None
    review_date: Optional[date] = None
    comments: Optional[str] = None


class BenevolenceReviewRead(BenevolenceReviewBase):
    """Schema for reading a benevolence review."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
