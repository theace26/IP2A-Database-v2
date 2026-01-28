"""Service for dues rate operations."""
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.db.enums import MemberClassification
from src.models.dues_rate import DuesRate
from src.schemas.dues_rate import DuesRateCreate, DuesRateUpdate


def get_rate(db: Session, rate_id: int) -> Optional[DuesRate]:
    """Get a dues rate by ID."""
    return db.query(DuesRate).filter(DuesRate.id == rate_id).first()


def get_current_rate(db: Session, classification: MemberClassification) -> Optional[DuesRate]:
    """Get current active dues rate for a classification."""
    today = date.today()
    return db.query(DuesRate).filter(
        DuesRate.classification == classification,
        DuesRate.effective_date <= today,
        or_(DuesRate.end_date.is_(None), DuesRate.end_date >= today)
    ).order_by(DuesRate.effective_date.desc()).first()


def get_rate_for_date(
    db: Session, classification: MemberClassification, target_date: date
) -> Optional[DuesRate]:
    """Get dues rate for a specific date."""
    return db.query(DuesRate).filter(
        DuesRate.classification == classification,
        DuesRate.effective_date <= target_date,
        or_(DuesRate.end_date.is_(None), DuesRate.end_date >= target_date)
    ).order_by(DuesRate.effective_date.desc()).first()


def get_all_rates(
    db: Session,
    classification: Optional[MemberClassification] = None,
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100
) -> list[DuesRate]:
    """Get all dues rates with optional filtering."""
    query = db.query(DuesRate)

    if classification:
        query = query.filter(DuesRate.classification == classification)

    if active_only:
        today = date.today()
        query = query.filter(
            or_(DuesRate.end_date.is_(None), DuesRate.end_date >= today)
        )

    return query.order_by(
        DuesRate.classification, DuesRate.effective_date.desc()
    ).offset(skip).limit(limit).all()


def create_rate(db: Session, data: DuesRateCreate) -> DuesRate:
    """Create a new dues rate."""
    rate = DuesRate(**data.model_dump())
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


def update_rate(db: Session, rate_id: int, data: DuesRateUpdate) -> Optional[DuesRate]:
    """Update a dues rate."""
    rate = get_rate(db, rate_id)
    if not rate:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rate, field, value)

    db.commit()
    db.refresh(rate)
    return rate


def delete_rate(db: Session, rate_id: int) -> bool:
    """Delete a dues rate."""
    rate = get_rate(db, rate_id)
    if not rate:
        return False
    db.delete(rate)
    db.commit()
    return True
