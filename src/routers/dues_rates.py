"""Dues rates router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from src.db.session import get_db
from src.db.enums import MemberClassification
from src.schemas.dues_rate import (
    DuesRateCreate,
    DuesRateUpdate,
    DuesRateRead,
)
from src.services.dues_rate_service import (
    create_rate,
    get_rate,
    get_current_rate,
    get_rate_for_date,
    get_all_rates,
    update_rate,
    delete_rate,
)

router = APIRouter(prefix="/dues-rates", tags=["Dues Rates"])


@router.post("/", response_model=DuesRateRead, status_code=201)
def create(data: DuesRateCreate, db: Session = Depends(get_db)):
    """Create a new dues rate."""
    return create_rate(db, data)


@router.get("/current/{classification}", response_model=DuesRateRead)
def read_current(classification: MemberClassification, db: Session = Depends(get_db)):
    """Get the current active rate for a classification."""
    rate = get_current_rate(db, classification)
    if not rate:
        raise HTTPException(
            status_code=404,
            detail=f"No active rate found for classification {classification.value}"
        )
    return rate


@router.get("/for-date/{classification}", response_model=DuesRateRead)
def read_for_date(
    classification: MemberClassification,
    target_date: date = Query(..., description="Date to look up rate for"),
    db: Session = Depends(get_db)
):
    """Get the rate for a specific classification and date."""
    rate = get_rate_for_date(db, classification, target_date)
    if not rate:
        raise HTTPException(
            status_code=404,
            detail=f"No rate found for classification {classification.value} on {target_date}"
        )
    return rate


@router.get("/{rate_id}", response_model=DuesRateRead)
def read(rate_id: int, db: Session = Depends(get_db)):
    """Get a dues rate by ID."""
    rate = get_rate(db, rate_id)
    if not rate:
        raise HTTPException(status_code=404, detail="Dues rate not found")
    return rate


@router.get("/", response_model=List[DuesRateRead])
def list_all(
    classification: Optional[MemberClassification] = None,
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all dues rates with optional filtering."""
    return get_all_rates(db, classification, active_only, skip, limit)


@router.put("/{rate_id}", response_model=DuesRateRead)
def update(rate_id: int, data: DuesRateUpdate, db: Session = Depends(get_db)):
    """Update a dues rate."""
    rate = update_rate(db, rate_id, data)
    if not rate:
        raise HTTPException(status_code=404, detail="Dues rate not found")
    return rate


@router.delete("/{rate_id}")
def delete(rate_id: int, db: Session = Depends(get_db)):
    """Delete a dues rate."""
    if not delete_rate(db, rate_id):
        raise HTTPException(status_code=404, detail="Dues rate not found")
    return {"message": "Dues rate deleted"}
