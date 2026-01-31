"""Benevolence reviews router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.db.session import get_db
from src.schemas.benevolence_review import (
    BenevolenceReviewCreate,
    BenevolenceReviewUpdate,
    BenevolenceReviewRead,
)
from src.services.benevolence_review_service import (
    create_benevolence_review,
    get_benevolence_review,
    list_benevolence_reviews,
    list_reviews_for_application,
    update_benevolence_review,
    delete_benevolence_review,
)

router = APIRouter(prefix="/benevolence-reviews", tags=["Benevolence Reviews"])


@router.post("/", response_model=BenevolenceReviewRead, status_code=201)
def create(data: BenevolenceReviewCreate, db: Session = Depends(get_db)):
    """Create a new benevolence review."""
    return create_benevolence_review(db, data)


@router.get("/{review_id}", response_model=BenevolenceReviewRead)
def read(review_id: int, db: Session = Depends(get_db)):
    """Get a benevolence review by ID."""
    obj = get_benevolence_review(db, review_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Benevolence review not found")
    return obj


@router.get("/", response_model=List[BenevolenceReviewRead])
def list_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all benevolence reviews."""
    return list_benevolence_reviews(db, skip, limit)


@router.get(
    "/by-application/{application_id}",
    response_model=List[BenevolenceReviewRead],
)
def list_by_application(application_id: int, db: Session = Depends(get_db)):
    """List all reviews for a specific benevolence application."""
    return list_reviews_for_application(db, application_id)


@router.put("/{review_id}", response_model=BenevolenceReviewRead)
def update(
    review_id: int,
    data: BenevolenceReviewUpdate,
    db: Session = Depends(get_db),
):
    """Update a benevolence review."""
    obj = update_benevolence_review(db, review_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Benevolence review not found")
    return obj


@router.delete("/{review_id}")
def delete(review_id: int, db: Session = Depends(get_db)):
    """Delete a benevolence review."""
    if not delete_benevolence_review(db, review_id):
        raise HTTPException(status_code=404, detail="Benevolence review not found")
    return {"message": "Benevolence review deleted"}
