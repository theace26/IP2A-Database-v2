"""Dues adjustments router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from src.db.session import get_db
from src.db.enums import AdjustmentStatus
from src.schemas.dues_adjustment import (
    DuesAdjustmentCreate,
    DuesAdjustmentApprove,
    DuesAdjustmentRead,
)
from src.services.dues_adjustment_service import (
    create_adjustment,
    get_adjustment,
    get_pending_adjustments,
    get_member_adjustments,
    get_all_adjustments,
    approve_adjustment,
    delete_adjustment,
)

router = APIRouter(prefix="/dues-adjustments", tags=["Dues Adjustments"])


@router.post("/", response_model=DuesAdjustmentRead, status_code=201)
def create(
    data: DuesAdjustmentCreate,
    requested_by_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Create a new dues adjustment request."""
    return create_adjustment(db, data, requested_by_id)


@router.get("/pending", response_model=List[DuesAdjustmentRead])
def read_pending(db: Session = Depends(get_db)):
    """Get all pending adjustment requests."""
    return get_pending_adjustments(db)


@router.get("/member/{member_id}", response_model=List[DuesAdjustmentRead])
def read_member_adjustments(member_id: int, db: Session = Depends(get_db)):
    """Get all adjustments for a member."""
    return get_member_adjustments(db, member_id)


@router.get("/{adjustment_id}", response_model=DuesAdjustmentRead)
def read(adjustment_id: int, db: Session = Depends(get_db)):
    """Get an adjustment by ID."""
    adjustment = get_adjustment(db, adjustment_id)
    if not adjustment:
        raise HTTPException(status_code=404, detail="Adjustment not found")
    return adjustment


@router.get("/", response_model=List[DuesAdjustmentRead])
def list_all(
    status: Optional[AdjustmentStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all adjustments with optional filtering."""
    return get_all_adjustments(db, status, skip, limit)


@router.post("/{adjustment_id}/approve", response_model=DuesAdjustmentRead)
def approve(
    adjustment_id: int,
    data: DuesAdjustmentApprove,
    db: Session = Depends(get_db)
):
    """Approve or deny an adjustment."""
    adjustment = approve_adjustment(
        db,
        adjustment_id,
        data.approved_by_id,
        data.approved
    )
    if not adjustment:
        raise HTTPException(
            status_code=404,
            detail="Adjustment not found or not in pending status"
        )
    return adjustment


@router.delete("/{adjustment_id}")
def delete(adjustment_id: int, db: Session = Depends(get_db)):
    """Delete an adjustment (only if pending)."""
    if not delete_adjustment(db, adjustment_id):
        raise HTTPException(
            status_code=404,
            detail="Adjustment not found or not in pending status"
        )
    return {"message": "Adjustment deleted"}
