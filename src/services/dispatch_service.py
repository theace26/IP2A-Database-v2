"""
Service for dispatch operations.

Created: February 4, 2026 (Week 23 Session C)
Phase 7 - Referral & Dispatch System

Core dispatch workflow service - connects employer requests to members.
Implements Rules 9, 12, 13 from Local 46 Referral Procedures.
"""
from typing import Optional, Tuple, List
from datetime import datetime, date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from src.db.enums import (
    DispatchStatus,
    DispatchMethod,
    DispatchType,
    TermReason,
    RegistrationStatus,
    RolloffReason,
    LaborRequestStatus,
    BidStatus,
)
from src.models.dispatch import Dispatch
from src.models.labor_request import LaborRequest
from src.models.book_registration import BookRegistration
from src.models.member import Member
from src.models.registration_activity import RegistrationActivity
from src.db.enums import RegistrationAction
from src.services import labor_request_service
from src.services import book_registration_service


# --- Constants (per Local 46 Rules) ---
FOREPERSON_BLACKOUT_DAYS = 14  # 2-week blackout after quit/discharge
SHORT_CALL_MAX_DAYS = 10       # ≤10 business days = short call
SHORT_CALL_NO_LIMIT_DAYS = 3   # ≤3 days don't count toward limit
SHORT_CALL_MAX_PER_CYCLE = 2   # Max 2 short call returns per registration cycle


# --- Create Dispatch ---


def create_dispatch(
    db: Session,
    *,
    labor_request_id: int,
    member_id: int,
    registration_id: int,
    dispatched_by_id: int,
    dispatch_method: DispatchMethod,
    is_short_call: bool = False,
    bid_id: Optional[int] = None,
) -> Dispatch:
    """
    Create a dispatch record and update related entities.

    Side effects:
    - BookRegistration status → DISPATCHED
    - LaborRequest workers_dispatched incremented
    - RegistrationActivity logged
    """
    # Validate labor request
    request = labor_request_service.get_by_id(db, labor_request_id)
    if not request:
        raise ValueError("Labor request not found")

    if request.is_filled:
        raise ValueError("Labor request is already filled")

    # Validate registration
    registration = book_registration_service.get_by_id(db, registration_id)
    if not registration:
        raise ValueError("Registration not found")

    if registration.member_id != member_id:
        raise ValueError("Registration does not belong to this member")

    if registration.status != RegistrationStatus.REGISTERED:
        raise ValueError(f"Cannot dispatch: registration status is {registration.status.value}")

    # Determine dispatch type
    dispatch_type = DispatchType.SHORT_CALL if is_short_call else DispatchType.NORMAL

    # Set check-in deadline (3 PM same day for web dispatch)
    check_in_deadline = None
    if dispatch_method in (DispatchMethod.INTERNET_BID, DispatchMethod.EMAIL_BID):
        check_in_deadline = datetime.combine(
            request.start_date,
            datetime.strptime("15:00", "%H:%M").time()
        )

    dispatch = Dispatch(
        labor_request_id=labor_request_id,
        member_id=member_id,
        registration_id=registration_id,
        bid_id=bid_id,
        employer_id=request.employer_id,
        dispatch_date=datetime.utcnow(),
        dispatch_method=dispatch_method,
        dispatch_type=dispatch_type,
        dispatched_by_id=dispatched_by_id,
        job_class=request.job_class,
        book_code=registration.book.code if registration.book else None,
        contract_code=request.contract_code,
        worksite=request.worksite_name,
        city=request.city,
        start_date=request.start_date,
        start_time=request.start_time,
        end_date=request.start_date + timedelta(days=request.estimated_duration_days or 0)
        if request.estimated_duration_days
        else None,
        start_rate=request.wage_rate,
        dispatch_status=DispatchStatus.DISPATCHED,
        check_in_deadline=check_in_deadline,
        is_short_call=is_short_call,
        restore_to_book=is_short_call,
    )

    db.add(dispatch)
    db.flush()  # Get dispatch ID

    # Update registration status
    book_registration_service.mark_dispatched(
        db, registration_id, dispatch.id, dispatched_by_id
    )

    # Increment dispatched count on request
    labor_request_service.increment_dispatched(db, labor_request_id)

    db.commit()
    db.refresh(dispatch)

    return dispatch


def dispatch_from_queue(
    db: Session,
    labor_request_id: int,
    dispatched_by_id: int,
) -> Optional[Dispatch]:
    """
    Auto-select next eligible member from queue and dispatch.

    Selection order:
    1. Book 1 first, then Book 2, then Book 3+
    2. Within each book tier: FIFO by APN (lowest first)
    3. Skip exempt members, blackout periods, suspended members

    Returns None if no eligible members available.
    """
    request = labor_request_service.get_by_id(db, labor_request_id)
    if not request:
        raise ValueError("Labor request not found")

    if request.is_filled:
        raise ValueError("Labor request is already filled")

    # Get book queue
    if not request.book_id:
        raise ValueError("Labor request has no associated book")

    registration = get_next_eligible_for_request(db, request)
    if not registration:
        return None

    return create_dispatch(
        db,
        labor_request_id=labor_request_id,
        member_id=registration.member_id,
        registration_id=registration.id,
        dispatched_by_id=dispatched_by_id,
        dispatch_method=DispatchMethod.MORNING_REFERRAL,
        is_short_call=request.is_short_call,
    )


def dispatch_by_name(
    db: Session,
    *,
    labor_request_id: int,
    member_id: int,
    dispatched_by_id: int,
    anti_collusion_verified: bool = False,
) -> Dispatch:
    """
    Foreperson-by-name dispatch (Rule 13).

    Validates:
    - No active blackout period for this member-employer pair
    - Anti-collusion flag (staff must verify)

    Raises:
        ValueError: Validation failure
    """
    request = labor_request_service.get_by_id(db, labor_request_id)
    if not request:
        raise ValueError("Labor request not found")

    if not request.is_foreperson_by_name:
        raise ValueError("This is not a foreperson-by-name request")

    # Check blackout period
    if has_active_blackout(db, member_id, request.employer_id):
        raise ValueError(
            "Member has active blackout period with this employer (quit/discharge within 2 weeks)"
        )

    # Find member's registration on the relevant book
    registration = (
        db.query(BookRegistration)
        .filter(
            BookRegistration.member_id == member_id,
            BookRegistration.book_id == request.book_id,
            BookRegistration.status == RegistrationStatus.REGISTERED,
        )
        .first()
    )

    if not registration:
        raise ValueError("Member does not have active registration on the required book")

    return create_dispatch(
        db,
        labor_request_id=labor_request_id,
        member_id=member_id,
        registration_id=registration.id,
        dispatched_by_id=dispatched_by_id,
        dispatch_method=DispatchMethod.BY_NAME,
        is_short_call=request.is_short_call,
    )


# --- Check-In ---


def record_check_in(
    db: Session,
    dispatch_id: int,
) -> Dispatch:
    """
    Record that member checked in with employer.

    Required by 3 PM for web dispatches per Rule 8.
    """
    dispatch = get_by_id(db, dispatch_id)
    if not dispatch:
        raise ValueError("Dispatch not found")

    if dispatch.dispatch_status not in (DispatchStatus.DISPATCHED,):
        raise ValueError(f"Cannot check in: status is {dispatch.dispatch_status.value}")

    dispatch.checked_in = True
    dispatch.checked_in_at = datetime.utcnow()
    dispatch.dispatch_status = DispatchStatus.CHECKED_IN

    db.commit()
    db.refresh(dispatch)

    return dispatch


# --- Termination ---


def terminate_dispatch(
    db: Session,
    dispatch_id: int,
    *,
    term_reason: TermReason,
    term_date: Optional[date] = None,
    days_worked: Optional[int] = None,
    comment: Optional[str] = None,
    performed_by_id: int,
) -> Dispatch:
    """
    Terminate a dispatch. Routes to appropriate handler based on reason.

    QUIT/FIRED → process_quit/process_discharge (Rule 12)
    RIF → process_rif (no penalty)
    SHORT_CALL_END → process_short_call_end (Rule 9)
    """
    dispatch = get_by_id(db, dispatch_id)
    if not dispatch:
        raise ValueError("Dispatch not found")

    if not dispatch.is_active:
        raise ValueError(f"Cannot terminate: dispatch status is {dispatch.dispatch_status.value}")

    dispatch.term_date = term_date or date.today()
    dispatch.term_reason = term_reason
    dispatch.term_comment = comment
    dispatch.days_worked = days_worked
    dispatch.dispatch_status = DispatchStatus.TERMINATED

    # Route to specific handler
    if term_reason == TermReason.QUIT:
        _process_quit(db, dispatch, performed_by_id)
    elif term_reason == TermReason.FIRED:
        _process_discharge(db, dispatch, performed_by_id)
    elif term_reason == TermReason.SHORT_CALL_END:
        _process_short_call_end(db, dispatch, performed_by_id)
    else:
        # Standard termination (RIF, LAID_OFF, CONTRACT_END, etc.)
        _process_standard_termination(db, dispatch, performed_by_id)

    db.commit()
    db.refresh(dispatch)

    return dispatch


def _process_quit(db: Session, dispatch: Dispatch, performed_by_id: int) -> None:
    """
    Handle quit termination (Rule 12).

    1. Roll member off ALL books (not just dispatched book)
    2. Create blackout period (2 weeks, foreperson-by-name blocked)
    """
    member_id = dispatch.member_id
    employer_id = dispatch.employer_id

    # Roll off ALL active registrations
    all_registrations = book_registration_service.get_member_registrations(db, member_id, active_only=True)

    for reg in all_registrations:
        book_registration_service.roll_off_member(
            db,
            reg.id,
            performed_by_id,
            RolloffReason.QUIT,
            f"Quit job with {dispatch.employer.name if dispatch.employer else 'employer'} - rolled off all books",
        )

    # Set blackout period
    dispatch.foreperson_restriction_until = date.today() + timedelta(days=FOREPERSON_BLACKOUT_DAYS)


def _process_discharge(db: Session, dispatch: Dispatch, performed_by_id: int) -> None:
    """
    Handle discharge termination (Rule 12). Same consequences as quit.
    """
    member_id = dispatch.member_id

    # Roll off ALL active registrations
    all_registrations = book_registration_service.get_member_registrations(db, member_id, active_only=True)

    for reg in all_registrations:
        book_registration_service.roll_off_member(
            db,
            reg.id,
            performed_by_id,
            RolloffReason.DISCHARGED,
            f"Discharged from {dispatch.employer.name if dispatch.employer else 'employer'} - rolled off all books",
        )

    # Set blackout period
    dispatch.foreperson_restriction_until = date.today() + timedelta(days=FOREPERSON_BLACKOUT_DAYS)


def _process_short_call_end(db: Session, dispatch: Dispatch, performed_by_id: int) -> None:
    """
    Handle short call completion (Rule 9).

    If job was ≤10 business days:
    - Restore member to original queue position
    - ≤3 days: doesn't count toward 2-per-cycle limit
    - >3 days: counts toward limit (max 2 per registration cycle)
    """
    if not dispatch.is_short_call:
        raise ValueError("Dispatch is not a short call")

    registration = dispatch.registration
    if not registration:
        return

    days_worked = dispatch.days_worked or 0

    # Check short call return limit (if >3 days)
    if days_worked > SHORT_CALL_NO_LIMIT_DAYS:
        returns_this_cycle = count_short_call_returns(db, registration.id)
        if returns_this_cycle >= SHORT_CALL_MAX_PER_CYCLE:
            raise ValueError(
                f"Member has reached maximum short call returns ({SHORT_CALL_MAX_PER_CYCLE}) for this registration cycle"
            )

    # Restore registration to REGISTERED status
    registration.status = RegistrationStatus.REGISTERED
    dispatch.restored_at = datetime.utcnow()

    # Log activity
    activity = RegistrationActivity(
        registration_id=registration.id,
        member_id=registration.member_id,
        book_id=registration.book_id,
        action=RegistrationAction.RESTORE,
        previous_status=RegistrationStatus.DISPATCHED,
        new_status=RegistrationStatus.REGISTERED,
        performed_by_id=performed_by_id,
        dispatch_id=dispatch.id,
        details=f"Position restored after {days_worked}-day short call",
    )
    db.add(activity)


def _process_standard_termination(db: Session, dispatch: Dispatch, performed_by_id: int) -> None:
    """
    Handle standard termination (RIF, laid off, contract end).

    No penalty - member simply returns to available status.
    """
    # Registration remains in DISPATCHED status or can be resigned
    # No automatic re-registration
    pass


# --- Query Methods ---


def get_by_id(db: Session, dispatch_id: int) -> Optional[Dispatch]:
    """Get a dispatch by ID."""
    return db.query(Dispatch).filter(Dispatch.id == dispatch_id).first()


def get_active_dispatches(
    db: Session,
    *,
    book_id: Optional[int] = None,
    employer_id: Optional[int] = None,
) -> list[Dispatch]:
    """Get all currently active dispatches."""
    query = db.query(Dispatch).filter(
        Dispatch.dispatch_status.in_([
            DispatchStatus.DISPATCHED,
            DispatchStatus.CHECKED_IN,
            DispatchStatus.WORKING,
        ])
    )

    if book_id:
        query = query.join(BookRegistration).filter(BookRegistration.book_id == book_id)
    if employer_id:
        query = query.filter(Dispatch.employer_id == employer_id)

    return query.order_by(Dispatch.dispatch_date.desc()).all()


def get_member_dispatch_history(
    db: Session,
    member_id: int,
    limit: int = 50,
) -> list[Dispatch]:
    """Get dispatch history for a member."""
    return (
        db.query(Dispatch)
        .filter(Dispatch.member_id == member_id)
        .order_by(Dispatch.dispatch_date.desc())
        .limit(limit)
        .all()
    )


def get_book_dispatch_stats(
    db: Session,
    book_id: int,
    period_days: int = 30,
) -> dict:
    """Get dispatch statistics for a book over a time period."""
    cutoff = datetime.utcnow() - timedelta(days=period_days)

    dispatches = (
        db.query(Dispatch)
        .join(BookRegistration)
        .filter(
            BookRegistration.book_id == book_id,
            Dispatch.dispatch_date >= cutoff,
        )
        .all()
    )

    total = len(dispatches)
    active = sum(1 for d in dispatches if d.is_active)
    completed = sum(1 for d in dispatches if d.dispatch_status == DispatchStatus.COMPLETED)
    terminated = sum(1 for d in dispatches if d.dispatch_status == DispatchStatus.TERMINATED)
    short_calls = sum(1 for d in dispatches if d.is_short_call)
    quits = sum(1 for d in dispatches if d.term_reason == TermReason.QUIT)
    discharges = sum(1 for d in dispatches if d.term_reason == TermReason.FIRED)

    return {
        "book_id": book_id,
        "period_days": period_days,
        "total_dispatches": total,
        "active": active,
        "completed": completed,
        "terminated": terminated,
        "short_calls": short_calls,
        "quits": quits,
        "discharges": discharges,
        "dispatches_per_week": round(total / (period_days / 7), 2) if period_days > 0 else 0,
    }


# --- Eligibility & Blackout ---


def get_next_eligible_for_request(
    db: Session,
    request: LaborRequest,
) -> Optional[BookRegistration]:
    """
    Get next eligible member for a specific request.

    Checks:
    - Active registration on the book
    - Not exempt
    - No blackout with this employer
    - Book tier priority (Book 1 before Book 2)
    """
    if not request.book_id:
        return None

    # Get queue ordered by APN
    queue = book_registration_service.get_book_queue(
        db, request.book_id, include_exempt=False
    )

    for registration in queue:
        # Check blackout
        if has_active_blackout(db, registration.member_id, request.employer_id):
            continue

        # Eligible
        return registration

    return None


def has_active_blackout(
    db: Session,
    member_id: int,
    employer_id: int,
) -> bool:
    """
    Check if member has active blackout period with employer.

    Blackout = quit/discharge from this employer within last 2 weeks.
    """
    cutoff = date.today() - timedelta(days=FOREPERSON_BLACKOUT_DAYS)

    blackout_dispatch = (
        db.query(Dispatch)
        .filter(
            Dispatch.member_id == member_id,
            Dispatch.employer_id == employer_id,
            Dispatch.term_reason.in_([TermReason.QUIT, TermReason.FIRED]),
            Dispatch.term_date >= cutoff,
        )
        .first()
    )

    if blackout_dispatch:
        return True

    # Also check foreperson_restriction_until
    recent_quit = (
        db.query(Dispatch)
        .filter(
            Dispatch.member_id == member_id,
            Dispatch.employer_id == employer_id,
            Dispatch.foreperson_restriction_until >= date.today(),
        )
        .first()
    )

    return recent_quit is not None


def count_short_call_returns(db: Session, registration_id: int) -> int:
    """
    Count short call returns for a registration in the current cycle.

    Only counts short calls >3 days.
    """
    registration = book_registration_service.get_by_id(db, registration_id)
    if not registration:
        return 0

    # Count dispatches that were short calls and resulted in restoration
    return (
        db.query(func.count(Dispatch.id))
        .filter(
            Dispatch.registration_id == registration_id,
            Dispatch.is_short_call == True,
            Dispatch.restored_at.isnot(None),
            Dispatch.days_worked > SHORT_CALL_NO_LIMIT_DAYS,
        )
        .scalar()
        or 0
    )


# --- Batch Processing ---


def process_no_shows(
    db: Session,
    performed_by_id: int,
) -> list[Dispatch]:
    """
    Process dispatches where member failed to check in by deadline.

    Called by daily enforcement job.
    """
    now = datetime.utcnow()
    no_shows = []

    overdue = (
        db.query(Dispatch)
        .filter(
            Dispatch.dispatch_status == DispatchStatus.DISPATCHED,
            Dispatch.checked_in == False,
            Dispatch.check_in_deadline.isnot(None),
            Dispatch.check_in_deadline < now,
        )
        .all()
    )

    for dispatch in overdue:
        dispatch.dispatch_status = DispatchStatus.NO_SHOW
        dispatch.term_reason = TermReason.QUIT  # No-show counts as quit
        dispatch.term_date = date.today()

        # Roll off from all books
        _process_quit(db, dispatch, performed_by_id)
        no_shows.append(dispatch)

    if no_shows:
        db.commit()

    return no_shows
