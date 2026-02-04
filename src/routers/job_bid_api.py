"""
Job Bid API router.

Created: February 4, 2026 (Week 25 Session B)
Phase 7 - Referral & Dispatch System

Endpoints for online bidding workflow.
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.routers.dependencies.auth import StaffUser, get_current_user
from src.models.user import User
from src.db.enums import BidStatus
from src.services import job_bid_service

router = APIRouter(
    prefix="/api/v1/referral/bids",
    tags=["Job Bids"],
)


# --- Request Models ---


class JobBidCreate(BaseModel):
    """Request body for placing a bid."""
    member_id: int
    labor_request_id: int
    registration_id: int
    bid_method: str = "online"


# --- Endpoints ---


@router.post("", status_code=status.HTTP_201_CREATED)
def place_bid(
    data: JobBidCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Place a bid on a labor request.

    Rule 8: Only valid during bidding window (5:30 PM – 7:00 AM).
    Validates: active registration, not suspended, no duplicate bid.
    """
    try:
        return job_bid_service.place_bid(
            db,
            member_id=data.member_id,
            labor_request_id=data.labor_request_id,
            registration_id=data.registration_id,
            bid_method=data.bid_method,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{bid_id}")
def get_bid(
    bid_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Get bid detail."""
    bid = job_bid_service.get_by_id(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    return bid


@router.post("/{bid_id}/withdraw")
def withdraw_bid(
    bid_id: int,
    reason: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Withdraw a pending bid."""
    try:
        return job_bid_service.withdraw_bid(db, bid_id, reason=reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{bid_id}/accept")
def accept_bid(
    bid_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept a bid (staff action)."""
    try:
        return job_bid_service.accept_bid(db, bid_id, processed_by_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{bid_id}/reject")
def reject_bid(
    bid_id: int,
    reason: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reject an accepted bid. This counts as a quit (Rule 8/12).

    WARNING: 2nd rejection in 12 months = 1-year bidding suspension.
    """
    try:
        return job_bid_service.reject_bid(db, bid_id, reason=reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/request/{labor_request_id}")
def get_bids_for_request(
    labor_request_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
    status: Optional[str] = Query(None),
):
    """Get all bids for a labor request."""
    bid_status = None
    if status:
        try:
            bid_status = BidStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid bid status")

    return job_bid_service.get_bids_for_request(db, labor_request_id, status=bid_status)


@router.post("/request/{labor_request_id}/process")
def process_bids_for_request(
    labor_request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Process all pending bids for a request in FIFO order (by APN).

    Returns list of accepted bids.
    """
    try:
        return job_bid_service.process_bids(db, labor_request_id, processed_by_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/member/{member_id}")
def get_member_bid_history(
    member_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
    limit: int = Query(50),
    include_all: bool = Query(False),
):
    """Get bid history for a member."""
    return job_bid_service.get_member_bid_history(
        db, member_id, limit=limit, include_all=include_all
    )


@router.get("/member/{member_id}/pending")
def get_member_pending_bids(
    member_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Get all pending bids for a member."""
    return job_bid_service.get_pending_bids_for_member(db, member_id)


@router.get("/member/{member_id}/suspension")
def check_suspension(
    member_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """
    Check if member has active bidding suspension.

    Returns: is_suspended, suspended_until, rejections_in_window,
    next_rejection_causes_suspension.
    """
    return job_bid_service.check_suspension_status(db, member_id)
