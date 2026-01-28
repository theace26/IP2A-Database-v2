"""Dues periods router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from src.db.session import get_db
from src.schemas.dues_period import (
    DuesPeriodCreate,
    DuesPeriodUpdate,
    DuesPeriodRead,
    DuesPeriodClose,
)
from src.services.dues_period_service import (
    create_period,
    get_period,
    get_period_by_month,
    get_current_period,
    get_all_periods,
    update_period,
    close_period,
    generate_periods_for_year,
)

router = APIRouter(prefix="/dues-periods", tags=["Dues Periods"])


@router.post("/", response_model=DuesPeriodRead, status_code=201)
def create(data: DuesPeriodCreate, db: Session = Depends(get_db)):
    """Create a new dues period."""
    return create_period(db, data)


@router.post("/generate/{year}", response_model=List[DuesPeriodRead], status_code=201)
def generate_year(year: int, db: Session = Depends(get_db)):
    """Generate all 12 periods for a given year."""
    periods = generate_periods_for_year(db, year)
    if not periods:
        raise HTTPException(
            status_code=400,
            detail=f"Could not generate periods for {year}. Periods may already exist."
        )
    return periods


@router.get("/current", response_model=DuesPeriodRead)
def read_current(db: Session = Depends(get_db)):
    """Get the current (most recent open) period."""
    period = get_current_period(db)
    if not period:
        raise HTTPException(status_code=404, detail="No current period found")
    return period


@router.get("/by-month/{year}/{month}", response_model=DuesPeriodRead)
def read_by_month(year: int, month: int, db: Session = Depends(get_db)):
    """Get period by year and month."""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    period = get_period_by_month(db, year, month)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
    return period


@router.get("/{period_id}", response_model=DuesPeriodRead)
def read(period_id: int, db: Session = Depends(get_db)):
    """Get a dues period by ID."""
    period = get_period(db, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Dues period not found")
    return period


@router.get("/", response_model=List[DuesPeriodRead])
def list_all(
    year: Optional[int] = None,
    is_closed: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all dues periods with optional filtering."""
    return get_all_periods(db, year, is_closed, skip, limit)


@router.put("/{period_id}", response_model=DuesPeriodRead)
def update(period_id: int, data: DuesPeriodUpdate, db: Session = Depends(get_db)):
    """Update a dues period."""
    period = update_period(db, period_id, data)
    if not period:
        raise HTTPException(status_code=404, detail="Dues period not found")
    return period


@router.post("/{period_id}/close", response_model=DuesPeriodRead)
def close(period_id: int, data: DuesPeriodClose, db: Session = Depends(get_db)):
    """Close a dues period."""
    period = close_period(db, period_id, data.closed_by_id)
    if not period:
        raise HTTPException(
            status_code=404,
            detail="Dues period not found or already closed"
        )
    return period
