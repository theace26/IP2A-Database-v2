"""
Referral Books API router.

Created: February 4, 2026 (Week 25 Session A)
Phase 7 - Referral & Dispatch System

CRUD and query endpoints for referral books.
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.routers.dependencies.auth import StaffUser, AdminUser
from src.db.enums import BookClassification, BookRegion
from src.schemas.referral_book import (
    ReferralBookCreate,
    ReferralBookUpdate,
    ReferralBookRead,
    ReferralBookStats,
)
from src.services import referral_book_service
from src.services import queue_service

router = APIRouter(
    prefix="/api/v1/referral/books",
    tags=["Referral Books"],
)


@router.get("", response_model=List[ReferralBookRead])
def list_books(
    db: Session = Depends(get_db),
    user: StaffUser = None,
    classification: Optional[str] = Query(None, description="Filter by classification"),
    region: Optional[str] = Query(None, description="Filter by region"),
    active_only: bool = Query(True, description="Show only active books"),
):
    """List referral books with optional filters."""
    if classification and region:
        try:
            cls = BookClassification(classification)
            reg = BookRegion(region)
            return referral_book_service.get_by_classification_and_region(db, cls, reg)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid classification or region")
    elif classification:
        try:
            cls = BookClassification(classification)
            return referral_book_service.get_by_classification(db, cls)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid classification")
    elif region:
        try:
            reg = BookRegion(region)
            return referral_book_service.get_by_region(db, reg)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid region")
    elif active_only:
        return referral_book_service.get_all_active(db)
    else:
        return referral_book_service.get_all(db, include_inactive=True)


@router.get("/summary")
def get_all_books_summary(
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Summary of all books with registration counts."""
    return referral_book_service.get_all_books_summary(db)


@router.get("/classification-summary")
def get_classification_summary(
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Cross-book summary grouped by classification."""
    return queue_service.get_classification_summary(db)


@router.get("/{book_id}", response_model=ReferralBookRead)
def get_book(
    book_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Get referral book detail."""
    book = referral_book_service.get_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.get("/{book_id}/queue")
def get_book_queue(
    book_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
    include_exempt: bool = Query(False),
    limit: Optional[int] = Query(None, description="Limit number of results"),
):
    """Get the out-of-work queue for a book, ordered by APN (FIFO)."""
    book = referral_book_service.get_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return queue_service.get_queue_snapshot(db, book_id, include_exempt=include_exempt, limit=limit)


@router.get("/{book_id}/stats", response_model=ReferralBookStats)
def get_book_stats(
    book_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Get registration statistics for a book."""
    stats = referral_book_service.get_book_stats(db, book_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Book not found")
    return stats


@router.get("/{book_id}/depth")
def get_book_depth(
    book_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Get queue depth analytics for a book."""
    book = referral_book_service.get_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return queue_service.get_queue_depth(db, book_id)


@router.get("/{book_id}/utilization")
def get_book_utilization(
    book_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
    period_days: int = Query(30, description="Period in days"),
):
    """Get utilization statistics for a book."""
    book = referral_book_service.get_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return queue_service.get_book_utilization(db, book_id, period_days=period_days)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ReferralBookRead)
def create_book(
    data: ReferralBookCreate,
    db: Session = Depends(get_db),
    user: AdminUser = None,
):
    """Create a new referral book (admin only)."""
    try:
        return referral_book_service.create_book(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{book_id}", response_model=ReferralBookRead)
def update_book(
    book_id: int,
    data: ReferralBookUpdate,
    db: Session = Depends(get_db),
    user: AdminUser = None,
):
    """Update a referral book (admin only)."""
    book = referral_book_service.update_book(db, book_id, data)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.patch("/{book_id}/activate", response_model=ReferralBookRead)
def activate_book(
    book_id: int,
    db: Session = Depends(get_db),
    user: AdminUser = None,
):
    """Activate a deactivated book (admin only)."""
    book = referral_book_service.activate_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.patch("/{book_id}/deactivate", response_model=ReferralBookRead)
def deactivate_book(
    book_id: int,
    db: Session = Depends(get_db),
    user: AdminUser = None,
):
    """Deactivate a book (admin only)."""
    book = referral_book_service.deactivate_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book
