"""Service for dues period operations."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.models.dues_period import DuesPeriod
from src.schemas.dues_period import DuesPeriodCreate, DuesPeriodUpdate


def get_period(db: Session, period_id: int) -> Optional[DuesPeriod]:
    """Get a dues period by ID."""
    return db.query(DuesPeriod).filter(DuesPeriod.id == period_id).first()


def get_period_by_month(
    db: Session, year: int, month: int
) -> Optional[DuesPeriod]:
    """Get a dues period by year and month."""
    return db.query(DuesPeriod).filter(
        DuesPeriod.period_year == year,
        DuesPeriod.period_month == month
    ).first()


def get_current_period(db: Session) -> Optional[DuesPeriod]:
    """Get the current (most recent open) period."""
    return db.query(DuesPeriod).filter(
        DuesPeriod.is_closed == False
    ).order_by(DuesPeriod.period_year.desc(), DuesPeriod.period_month.desc()).first()


def get_all_periods(
    db: Session,
    year: Optional[int] = None,
    is_closed: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
) -> list[DuesPeriod]:
    """Get all dues periods with optional filtering."""
    query = db.query(DuesPeriod)

    if year:
        query = query.filter(DuesPeriod.period_year == year)

    if is_closed is not None:
        query = query.filter(DuesPeriod.is_closed == is_closed)

    return query.order_by(
        DuesPeriod.period_year.desc(),
        DuesPeriod.period_month.desc()
    ).offset(skip).limit(limit).all()


def create_period(db: Session, data: DuesPeriodCreate) -> DuesPeriod:
    """Create a new dues period."""
    period = DuesPeriod(**data.model_dump())
    db.add(period)
    db.commit()
    db.refresh(period)
    return period


def update_period(db: Session, period_id: int, data: DuesPeriodUpdate) -> Optional[DuesPeriod]:
    """Update a dues period."""
    period = get_period(db, period_id)
    if not period:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(period, field, value)

    db.commit()
    db.refresh(period)
    return period


def close_period(
    db: Session,
    period_id: int,
    user_id: int,
    notes: Optional[str] = None
) -> Optional[DuesPeriod]:
    """Close a dues period."""
    period = get_period(db, period_id)
    if not period or period.is_closed:
        return None

    period.is_closed = True
    period.closed_at = datetime.utcnow()
    period.closed_by_id = user_id
    if notes:
        period.notes = notes

    db.commit()
    db.refresh(period)
    return period


def generate_periods_for_year(db: Session, year: int) -> list[DuesPeriod]:
    """Generate all 12 monthly periods for a year."""
    periods = []
    for month in range(1, 13):
        existing = get_period_by_month(db, year, month)
        if existing:
            periods.append(existing)
            continue

        # Due on 1st of month, grace period ends on 15th
        due_date = date(year, month, 1)
        grace_end = date(year, month, 15)

        period = DuesPeriod(
            period_year=year,
            period_month=month,
            due_date=due_date,
            grace_period_end=grace_end
        )
        db.add(period)
        periods.append(period)

    db.commit()
    return periods
