"""
Book Registration API router.

Created: February 4, 2026 (Week 25 Session A)
Phase 7 - Referral & Dispatch System

Endpoints for member registration operations on referral books.
"""
from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.routers.dependencies.auth import StaffUser, get_current_user
from src.models.user import User
from src.db.enums import ExemptReason
from src.schemas.book_registration import (
    BookRegistrationCreate,
    BookRegistrationRead,
)
from src.services import book_registration_service
from src.services import queue_service

router = APIRouter(
    prefix="/api/v1/referral/registrations",
    tags=["Referral Registrations"],
)


# --- Request Models ---


class ExemptRequest(BaseModel):
    """Request body for granting exempt status."""
    exempt_reason: ExemptReason
    exempt_end_date: Optional[date] = None
    notes: Optional[str] = None


class RollOffRequest(BaseModel):
    """Request body for rolling off a member."""
    reason: Optional[str] = None
    notes: Optional[str] = None


# --- Endpoints ---


@router.post("", status_code=status.HTTP_201_CREATED)
def register_member(
    data: BookRegistrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Register a member on a referral book.

    Validates: one active registration per book per member (Rule 5).
    Assigns next APN in sequence.
    """
    try:
        return book_registration_service.register_member(
            db,
            member_id=data.member_id,
            book_id=data.book_id,
            performed_by_id=current_user.id,
            registration_method=data.registration_method or "in_person",
            notes=data.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{registration_id}")
def get_registration(
    registration_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Get registration detail."""
    registration = book_registration_service.get_by_id(db, registration_id)
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    return registration


@router.post("/{registration_id}/re-sign")
def re_sign_member(
    registration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-sign member for another 30-day cycle (Rule 7)."""
    try:
        return book_registration_service.re_sign_member(
            db, registration_id, performed_by_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{registration_id}/resign")
def resign_member(
    registration_id: int,
    reason: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Member voluntarily resigns from book."""
    try:
        return book_registration_service.resign_member(
            db, registration_id, performed_by_id=current_user.id, reason=reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{registration_id}/roll-off")
def roll_off_member(
    registration_id: int,
    data: RollOffRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Roll member off book (staff action)."""
    from src.db.enums import RolloffReason
    try:
        return book_registration_service.roll_off_member(
            db,
            registration_id,
            performed_by_id=current_user.id,
            reason=RolloffReason.MANUAL,
            notes=data.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{registration_id}/exempt")
def grant_exempt_status(
    registration_id: int,
    data: ExemptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Grant exempt status to a registration (Rule 14).

    Exempt reasons: military, medical, union_business, salting,
    jury_duty, training, other.
    """
    try:
        return book_registration_service.grant_exempt_status(
            db,
            registration_id,
            performed_by_id=current_user.id,
            reason=data.exempt_reason,
            end_date=data.exempt_end_date,
            notes=data.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{registration_id}/exempt")
def revoke_exempt_status(
    registration_id: int,
    reason: str = Query(..., description="Reason for revoking exempt status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke exempt status from a registration."""
    try:
        return book_registration_service.revoke_exempt_status(
            db, registration_id, performed_by_id=current_user.id, reason=reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{registration_id}/check-mark")
def record_check_mark(
    registration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a check mark for a member."""
    try:
        return book_registration_service.record_check_mark(
            db, registration_id, performed_by_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/member/{member_id}")
def get_member_registrations(
    member_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
    active_only: bool = Query(True),
):
    """Get all registrations for a member."""
    return book_registration_service.get_member_registrations(db, member_id, active_only=active_only)


@router.get("/member/{member_id}/status")
def get_member_queue_status(
    member_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """
    Get member's status on all books they're registered on.

    Returns position, APN, days_on_book, check marks, re-sign due date
    for each active registration.
    """
    return queue_service.get_member_queue_status(db, member_id)


@router.get("/member/{member_id}/wait-time")
def estimate_member_wait_time(
    member_id: int,
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Estimate wait time for a member across all their registrations."""
    registrations = book_registration_service.get_member_registrations(db, member_id, active_only=True)
    estimates = []
    for reg in registrations:
        estimate = queue_service.estimate_wait_time(db, reg.id)
        if "error" not in estimate:
            estimates.append(estimate)
    return estimates


@router.get("/expiring")
def get_expiring_registrations(
    db: Session = Depends(get_db),
    user: StaffUser = None,
    days: int = Query(7, description="Days until expiration"),
):
    """Get registrations approaching re-sign deadline."""
    return book_registration_service.get_registrations_expiring_soon(db, days_threshold=days)


@router.get("/reminders")
def get_re_sign_reminders(
    db: Session = Depends(get_db),
    user: StaffUser = None,
):
    """Get members who need to re-sign soon with details."""
    return book_registration_service.get_re_sign_reminders(db)
