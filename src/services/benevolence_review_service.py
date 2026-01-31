"""Benevolence review service for business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.benevolence_review import BenevolenceReview
from src.schemas.benevolence_review import (
    BenevolenceReviewCreate,
    BenevolenceReviewUpdate,
)


def create_benevolence_review(
    db: Session, data: BenevolenceReviewCreate
) -> BenevolenceReview:
    """Create a new benevolence review."""
    obj = BenevolenceReview(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_benevolence_review(
    db: Session, review_id: int
) -> Optional[BenevolenceReview]:
    """Get benevolence review by ID."""
    return (
        db.query(BenevolenceReview)
        .filter(BenevolenceReview.id == review_id)
        .first()
    )


def list_benevolence_reviews(
    db: Session, skip: int = 0, limit: int = 100
) -> List[BenevolenceReview]:
    """List benevolence reviews with pagination."""
    return db.query(BenevolenceReview).offset(skip).limit(limit).all()


def list_reviews_for_application(
    db: Session, application_id: int
) -> List[BenevolenceReview]:
    """List all reviews for a specific application."""
    return (
        db.query(BenevolenceReview)
        .filter(BenevolenceReview.application_id == application_id)
        .all()
    )


def update_benevolence_review(
    db: Session, review_id: int, data: BenevolenceReviewUpdate
) -> Optional[BenevolenceReview]:
    """Update a benevolence review."""
    obj = get_benevolence_review(db, review_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_benevolence_review(db: Session, review_id: int) -> bool:
    """Delete a benevolence review."""
    obj = get_benevolence_review(db, review_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
