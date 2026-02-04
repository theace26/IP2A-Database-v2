"""
Service for referral book operations.

Created: February 4, 2026 (Week 22 Session A)
Phase 7 - Referral & Dispatch System

Handles referral book queries, filtering, and administrative operations.
"""
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from src.db.enums import BookClassification, BookRegion, RegistrationStatus
from src.models.referral_book import ReferralBook
from src.models.book_registration import BookRegistration
from src.schemas.referral_book import (
    ReferralBookCreate,
    ReferralBookUpdate,
    ReferralBookStats,
)


# --- Query Methods ---


def get_by_id(db: Session, book_id: int) -> Optional[ReferralBook]:
    """Get a single book by ID."""
    return db.query(ReferralBook).filter(ReferralBook.id == book_id).first()


def get_by_code(db: Session, code: str) -> Optional[ReferralBook]:
    """Get a single book by unique code (e.g., 'WIRE_SEA_1')."""
    return db.query(ReferralBook).filter(ReferralBook.code == code).first()


def get_all_active(db: Session) -> list[ReferralBook]:
    """Get all active referral books, ordered by classification then region."""
    return (
        db.query(ReferralBook)
        .filter(ReferralBook.is_active == True)
        .order_by(ReferralBook.classification, ReferralBook.region, ReferralBook.book_number)
        .all()
    )


def get_all(
    db: Session,
    include_inactive: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> list[ReferralBook]:
    """Get all referral books with pagination."""
    query = db.query(ReferralBook)
    if not include_inactive:
        query = query.filter(ReferralBook.is_active == True)
    return (
        query.order_by(
            ReferralBook.classification, ReferralBook.region, ReferralBook.book_number
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_by_classification(
    db: Session, classification: BookClassification
) -> list[ReferralBook]:
    """Get all books for a given classification (e.g., inside_wireperson)."""
    return (
        db.query(ReferralBook)
        .filter(
            ReferralBook.classification == classification, ReferralBook.is_active == True
        )
        .order_by(ReferralBook.region, ReferralBook.book_number)
        .all()
    )


def get_by_region(db: Session, region: BookRegion) -> list[ReferralBook]:
    """Get all books in a given region (e.g., seattle)."""
    return (
        db.query(ReferralBook)
        .filter(ReferralBook.region == region, ReferralBook.is_active == True)
        .order_by(ReferralBook.classification, ReferralBook.book_number)
        .all()
    )


def get_by_classification_and_region(
    db: Session, classification: BookClassification, region: BookRegion
) -> list[ReferralBook]:
    """Get books matching both classification and region."""
    return (
        db.query(ReferralBook)
        .filter(
            ReferralBook.classification == classification,
            ReferralBook.region == region,
            ReferralBook.is_active == True,
        )
        .order_by(ReferralBook.book_number)
        .all()
    )


# --- Book Statistics ---


def get_book_stats(db: Session, book_id: int) -> Optional[ReferralBookStats]:
    """
    Get registration statistics for a book.

    Returns stats for:
    - total_registered: Total registrations ever
    - active_count: Currently registered (REGISTERED status)
    - dispatched_count: Currently dispatched
    - with_check_mark: Active with check mark
    - without_check_mark: Active without check mark
    - exempt_count: Currently exempt
    """
    book = get_by_id(db, book_id)
    if not book:
        return None

    # Count queries
    total = (
        db.query(func.count(BookRegistration.id))
        .filter(BookRegistration.book_id == book_id)
        .scalar()
    )

    active = (
        db.query(func.count(BookRegistration.id))
        .filter(
            BookRegistration.book_id == book_id,
            BookRegistration.status == RegistrationStatus.REGISTERED,
        )
        .scalar()
    )

    dispatched = (
        db.query(func.count(BookRegistration.id))
        .filter(
            BookRegistration.book_id == book_id,
            BookRegistration.status == RegistrationStatus.DISPATCHED,
        )
        .scalar()
    )

    with_check = (
        db.query(func.count(BookRegistration.id))
        .filter(
            BookRegistration.book_id == book_id,
            BookRegistration.status == RegistrationStatus.REGISTERED,
            BookRegistration.has_check_mark == True,
        )
        .scalar()
    )

    without_check = (
        db.query(func.count(BookRegistration.id))
        .filter(
            BookRegistration.book_id == book_id,
            BookRegistration.status == RegistrationStatus.REGISTERED,
            BookRegistration.has_check_mark == False,
        )
        .scalar()
    )

    exempt = (
        db.query(func.count(BookRegistration.id))
        .filter(
            BookRegistration.book_id == book_id,
            BookRegistration.status == RegistrationStatus.REGISTERED,
            BookRegistration.is_exempt == True,
        )
        .scalar()
    )

    return ReferralBookStats(
        book_id=book_id,
        book_name=book.name,
        book_code=book.code,
        total_registered=total or 0,
        active_count=active or 0,
        dispatched_count=dispatched or 0,
        with_check_mark=with_check or 0,
        without_check_mark=without_check or 0,
        exempt_count=exempt or 0,
    )


def get_all_books_summary(db: Session) -> list[dict]:
    """
    Get summary stats for ALL active books.

    Used by the dispatch dashboard. Returns list of dicts with:
    - book info (id, name, code, classification, region, book_number)
    - active_registrations count
    - total_registrations count
    """
    books = get_all_active(db)
    summaries = []

    for book in books:
        active_count = (
            db.query(func.count(BookRegistration.id))
            .filter(
                BookRegistration.book_id == book.id,
                BookRegistration.status == RegistrationStatus.REGISTERED,
            )
            .scalar()
            or 0
        )

        total_count = (
            db.query(func.count(BookRegistration.id))
            .filter(BookRegistration.book_id == book.id)
            .scalar()
            or 0
        )

        summaries.append(
            {
                "id": book.id,
                "name": book.name,
                "code": book.code,
                "classification": book.classification.value,
                "region": book.region.value,
                "book_number": book.book_number,
                "referral_start_time": book.referral_start_time,
                "is_active": book.is_active,
                "internet_bidding_enabled": book.internet_bidding_enabled,
                "active_registrations": active_count,
                "total_registrations": total_count,
            }
        )

    return summaries


# --- CRUD Operations ---


def create_book(db: Session, data: ReferralBookCreate) -> ReferralBook:
    """Create a new referral book."""
    book = ReferralBook(**data.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(
    db: Session, book_id: int, data: ReferralBookUpdate
) -> Optional[ReferralBook]:
    """Update a referral book."""
    book = get_by_id(db, book_id)
    if not book:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(book, field, value)

    db.commit()
    db.refresh(book)
    return book


# --- Administrative Operations ---


def activate_book(db: Session, book_id: int) -> Optional[ReferralBook]:
    """Reactivate a deactivated book."""
    book = get_by_id(db, book_id)
    if not book:
        return None

    book.is_active = True
    db.commit()
    db.refresh(book)
    return book


def deactivate_book(db: Session, book_id: int) -> Optional[ReferralBook]:
    """
    Deactivate a book.

    Does NOT remove registrations - members remain registered but
    book won't appear in active lists.
    """
    book = get_by_id(db, book_id)
    if not book:
        return None

    book.is_active = False
    db.commit()
    db.refresh(book)
    return book


def update_book_settings(
    db: Session,
    book_id: int,
    max_days_on_book: Optional[int] = None,
    re_sign_days: Optional[int] = None,
    grace_period_days: Optional[int] = None,
    internet_bidding_enabled: Optional[bool] = None,
) -> Optional[ReferralBook]:
    """Update configurable book settings."""
    book = get_by_id(db, book_id)
    if not book:
        return None

    if max_days_on_book is not None:
        book.max_days_on_book = max_days_on_book
    if re_sign_days is not None:
        book.re_sign_days = re_sign_days
    if grace_period_days is not None:
        book.grace_period_days = grace_period_days
    if internet_bidding_enabled is not None:
        book.internet_bidding_enabled = internet_bidding_enabled

    db.commit()
    db.refresh(book)
    return book
