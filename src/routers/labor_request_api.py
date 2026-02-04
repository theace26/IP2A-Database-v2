"""
Labor Request API router.

Created: February 4, 2026 (Week 25 Session B)
Phase 7 - Referral & Dispatch System

Endpoints for employer labor requests.
"""
from typing import Optional, List
from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.routers.dependencies.auth import StaffUser, get_current_user
from src.models.user import User
from src.db.enums import AgreementType
from src.services import labor_request_service

router = APIRouter(
    prefix="/api/v1/referral/requests",
    tags=["Labor Requests"],
)


# --- Request Models ---


class LaborRequestCreate(BaseModel):
    """Request body for creating a labor request."""
    employer_id: int
    book_id: int
    workers_requested: int
    start_date: date
    worksite_name: Optional[str] = None
    worksite_address: Optional[str] = None
    city: Optional[str] = None
    start_time: Optional[time] = None
    estimated_duration_days: Optional[int] = None
    is_short_call: Optional[bool] = None
    short_call_days: Optional[int] = None
    is_foreperson_by_name: bool = False
    foreperson_member_id: Optional[int] = None
    requirements: Optional[str] = None
    comments: Optional[str] = None
    agreement_type: Optional[AgreementType] = None
    allows_online_bidding: bool = True


class LaborRequestUpdate(BaseModel):
    """Request body for updating a labor request."""
    workers_requested: Optional[int] = None
    worksite_name: Optional[str] = None
    worksite_address: Optional[str] = None
    city: Optional[str] = None
    start_time: Optional[time] = None
    estimated_duration_days: Optional[int] = None
    requirements: Optional[str] = None
    comments: Optional[str] = None


# --- Endpoints ---


@router.post("", status_code=status.HTTP_201_CREATED)
def create_request(
    data: LaborRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new labor request from an employer.

    Validates cutoff time (Rule 3): requests after 3 PM go to next day.
    Pre-calculates generates_checkmark flag (Rule 11).
    """
    try:
        return labor_request_service.create_request(
            db,
            employer_id=data.employer_id,
            book_id=data.book_id,
            workers_requested=data.workers_requested,
            start_date=data.start_date,
            created_by_id=current_user.id,
            worksite_name=data.worksite_name,
            worksite_address=data.worksite_address,
            city=data.city,
            start_time=data.start_time,
            estimated_duration_days=data.estimated_duration_days,
            is_short_call=data.is_short_call,
            short_call_days=data.short_call_days,
            is_foreperson_by_name=data.is_foreperson_by_name,
            foreperson_member_id=data.foreperson_member_id,
            requirements=data.requirements,
            comments=data.comments,
            agreement_type=data.agreement_type,
            allows_online_bidding=data.allows_online_bidding,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
def list_requests(
    db: Session = Depends(get_db),
    user: StaffUser = None,
    book_id: Optional[int] = Query(None),
    employer_id: Optional[int] = Query(None),
    classification: Optional[str] = Query(None),
    include_filled: bool = Query(False),
):
    """List labor requests with optional filters."""
    from src.db.enums import BookClassification

    cls = None
    if classification:
        try:
            cls = BookClassification(classification)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid classification")

    return labor_request_service.get_open_requests(
        db,
        book_id=book_id,
        classification=cls,
        employer_id=employer_id,
    )


@router.get("/morning")
def get_morning_requests(
    db: Session = Depends(get_db),
    user: StaffUser = None,
    target_date: Optional[date] = Query(None, description="Date in YYYY-MM-DD format"),
):
    """
    Get all requests ready for morning referral, ordered by classification time.

    Rule 2: Wire 8:30 AM → S&C/Marine/Stock/LFM/Residential 9:00 AM → Tradeshow 9:30 AM
    """
    return labor_request_service.get_requests_for_morning(db, target_date=target_date)


@router.get("/open")
def get_open_requests(
    db: Session = Depends(get_db),
    user: StaffUser = None,
    book_id: Optional[int] = Query(None),
):
    """List all unfilled labor requests."""
    return labor_request_service.get_open_requests(db, book_id=book_id)


@router.get("/employer/{employer_id}")
def get_employer_requests(
    employer_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
    include_filled: bool = Query(False),
    limit: int = Query(50),
):
    """Get request history for an employer."""
    return labor_request_service.get_employer_requests(
        db, employer_id, include_filled=include_filled, limit=limit
    )


@router.get("/{request_id}")
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Get labor request detail."""
    request = labor_request_service.get_by_id(db, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Labor request not found")
    return request


@router.put("/{request_id}")
def update_request(
    request_id: int,
    data: LaborRequestUpdate,
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Update an open labor request."""
    try:
        return labor_request_service.update_request(
            db, request_id, **data.dict(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{request_id}/cancel")
def cancel_request(
    request_id: int,
    reason: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Cancel an open labor request."""
    try:
        return labor_request_service.cancel_request(db, request_id, reason=reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{request_id}/expire")
def expire_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Mark a labor request as expired."""
    try:
        return labor_request_service.expire_request(db, request_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{request_id}/bidding-status")
def check_bidding_status(
    request_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Check if bidding is currently open for a request."""
    request = labor_request_service.get_by_id(db, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Labor request not found")

    is_open = labor_request_service.validate_bidding_window(request)

    return {
        "request_id": request_id,
        "is_bidding_open": is_open,
        "allows_online_bidding": request.allows_online_bidding,
        "bidding_opens_at": request.bidding_opens_at,
        "bidding_closes_at": request.bidding_closes_at,
    }


@router.get("/{request_id}/check-mark-status")
def get_check_mark_status(
    request_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Check if this request generates check marks (Rule 11)."""
    request = labor_request_service.get_by_id(db, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Labor request not found")

    generates, reason = labor_request_service.determine_check_mark(request)

    return {
        "request_id": request_id,
        "generates_check_mark": generates,
        "no_check_mark_reason": reason.value if reason else None,
    }
