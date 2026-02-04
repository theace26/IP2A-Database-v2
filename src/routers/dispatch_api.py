"""
Dispatch API router.

Created: February 4, 2026 (Week 25 Session C)
Phase 7 - Referral & Dispatch System

Endpoints for dispatch workflow, queue management, and enforcement.
"""
from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.routers.dependencies.auth import StaffUser, AdminUser, get_current_user
from src.models.user import User
from src.db.enums import DispatchMethod, TermReason
from src.services import dispatch_service
from src.services import queue_service
from src.services import enforcement_service

router = APIRouter(
    prefix="/api/v1/referral",
    tags=["Dispatch"],
)


# --- Request Models ---


class DispatchCreate(BaseModel):
    """Request body for creating a dispatch."""
    labor_request_id: int
    member_id: Optional[int] = None
    registration_id: Optional[int] = None


class DispatchByNameRequest(BaseModel):
    """Request body for foreperson-by-name dispatch."""
    labor_request_id: int
    member_id: int
    anti_collusion_verified: bool = False


class DispatchTerminate(BaseModel):
    """Request body for terminating a dispatch."""
    term_reason: TermReason
    term_date: Optional[date] = None
    days_worked: Optional[int] = None
    comment: Optional[str] = None


# --- Dispatch Endpoints ---


@router.post("/dispatch", status_code=status.HTTP_201_CREATED)
def create_dispatch_from_queue(
    data: DispatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dispatch next eligible member from queue to a labor request.

    Selects member by FIFO (APN order), Book 1 before Book 2.
    Creates dispatch record, marks registration as DISPATCHED.
    """
    try:
        dispatch = dispatch_service.dispatch_from_queue(
            db, data.labor_request_id, dispatched_by_id=current_user.id
        )
        if not dispatch:
            raise HTTPException(
                status_code=404,
                detail="No eligible members available for dispatch"
            )
        return dispatch
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/dispatch/by-name", status_code=status.HTTP_201_CREATED)
def dispatch_by_name(
    data: DispatchByNameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Foreperson-by-name dispatch (Rule 13).

    Validates no active blackout period and anti-collusion rules.
    """
    try:
        return dispatch_service.dispatch_by_name(
            db,
            labor_request_id=data.labor_request_id,
            member_id=data.member_id,
            dispatched_by_id=current_user.id,
            anti_collusion_verified=data.anti_collusion_verified,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/dispatch/{dispatch_id}")
def get_dispatch(
    dispatch_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Get dispatch detail."""
    dispatch = dispatch_service.get_by_id(db, dispatch_id)
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    return dispatch


@router.post("/dispatch/{dispatch_id}/check-in")
def record_check_in(
    dispatch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record member check-in with employer (required by 3 PM for web dispatches)."""
    try:
        return dispatch_service.record_check_in(db, dispatch_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/dispatch/{dispatch_id}/terminate")
def terminate_dispatch(
    dispatch_id: int,
    data: DispatchTerminate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Terminate a dispatch.

    Routes by reason:
    - QUIT/FIRED: Roll off ALL books, 2-week blackout (Rule 12)
    - RIF: Standard termination, no penalty
    - SHORT_CALL_END: Restore queue position (Rule 9)
    """
    try:
        return dispatch_service.terminate_dispatch(
            db,
            dispatch_id,
            term_reason=data.term_reason,
            term_date=data.term_date,
            days_worked=data.days_worked,
            comment=data.comment,
            performed_by_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/dispatch/active")
def get_active_dispatches(
    db: Session = Depends(get_db),
    user: StaffUser = None,
    book_id: Optional[int] = Query(None),
    employer_id: Optional[int] = Query(None),
):
    """List all currently active dispatches."""
    return dispatch_service.get_active_dispatches(db, book_id=book_id, employer_id=employer_id)


@router.get("/dispatch/member/{member_id}")
def get_member_dispatch_history(
    member_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
    limit: int = Query(50),
):
    """Get dispatch history for a member."""
    return dispatch_service.get_member_dispatch_history(db, member_id, limit=limit)


@router.get("/dispatch/book/{book_id}/stats")
def get_book_dispatch_stats(
    book_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
    period_days: int = Query(30),
):
    """Get dispatch statistics for a book."""
    return dispatch_service.get_book_dispatch_stats(db, book_id, period_days=period_days)


# --- Queue Endpoints ---


@router.get("/queue/{book_id}")
def get_queue_snapshot(
    book_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
    include_exempt: bool = Query(False),
    limit: Optional[int] = Query(None),
):
    """Full queue snapshot for a book, ordered by APN."""
    return queue_service.get_queue_snapshot(db, book_id, include_exempt=include_exempt, limit=limit)


@router.get("/queue/{book_id}/depth")
def get_queue_depth(
    book_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Queue depth analytics: total, active, exempt, by tier."""
    return queue_service.get_queue_depth(db, book_id)


@router.get("/queue/{book_id}/dispatch-rate")
def get_dispatch_rate(
    book_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
    period: str = Query("week", description="Period: 'week' or 'month'"),
):
    """Get dispatch rate for a book."""
    return queue_service.get_dispatch_rate(db, book_id, period=period)


@router.get("/queue/daily-activity")
def get_daily_activity_log(
    db: Session = Depends(get_db),
    user: StaffUser = None,
    target_date: Optional[date] = Query(None),
):
    """All queue changes for a given day."""
    return queue_service.get_daily_activity_log(db, target_date=target_date)


# --- Enforcement Endpoints ---


@router.post("/admin/enforcement/run")
def run_enforcement(
    db: Session = Depends(get_db),
    user: AdminUser = None,
    dry_run: bool = Query(False, description="Preview without making changes"),
):
    """
    Trigger daily enforcement run.

    Processes: expired re-signs, expired exemptions, expired blackouts,
    expired suspensions, unfilled requests.
    """
    return enforcement_service.daily_enforcement_run(db, dry_run=dry_run, performed_by_id=user.id)


@router.get("/admin/enforcement/preview")
def preview_enforcement(
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Preview what enforcement would do without making changes."""
    return enforcement_service.get_enforcement_report(db)


@router.get("/admin/enforcement/pending")
def get_pending_enforcements(
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Get counts of items pending enforcement."""
    return enforcement_service.get_pending_enforcements(db)


@router.post("/admin/enforcement/{enforcement_type}")
def run_specific_enforcement(
    enforcement_type: str,
    db: Session = Depends(get_db),
    user: AdminUser = None,
    dry_run: bool = Query(False),
):
    """
    Run a specific enforcement type.

    Types: 're_sign', 'requests', 'exemptions', 'bids', 'check_marks'
    """
    try:
        return enforcement_service.run_specific_enforcement(
            db, enforcement_type, dry_run=dry_run, performed_by_id=user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/admin/re-sign-reminders")
def get_re_sign_reminders(
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """List members with re-sign due within 7 days."""
    return enforcement_service.send_re_sign_reminders(db)


# --- Blackout Check ---


@router.get("/blackout/check")
def check_blackout(
    member_id: int,
    employer_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Check if a member has an active blackout with an employer."""
    has_blackout = dispatch_service.has_active_blackout(db, member_id, employer_id)
    return {
        "member_id": member_id,
        "employer_id": employer_id,
        "has_active_blackout": has_blackout,
    }
