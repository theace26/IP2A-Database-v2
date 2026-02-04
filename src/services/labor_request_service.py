"""
Service for labor request operations.

Created: February 4, 2026 (Week 23 Session A)
Phase 7 - Referral & Dispatch System

Manages employer labor requests - the demand side of the dispatch equation.
Implements Rules 2, 3, 4, 11 from Local 46 Referral Procedures.
"""
from typing import Optional, Tuple
from datetime import datetime, date, time, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from src.db.enums import (
    LaborRequestStatus,
    BookClassification,
    BookRegion,
    NoCheckMarkReason,
    AgreementType,
)
from src.models.labor_request import LaborRequest
from src.models.referral_book import ReferralBook
from src.models.organization import Organization
from src.services import referral_book_service


# --- Time Constants (per Local 46 Rules) ---
MORNING_CUTOFF = time(15, 0)      # 3:00 PM cutoff for next-morning requests
BIDDING_OPEN = time(17, 30)       # 5:30 PM online bidding opens
BIDDING_CLOSE = time(7, 0)        # 7:00 AM online bidding closes
EMPLOYER_CHECKIN = time(15, 0)    # 3:00 PM check-in deadline
EARLY_START_THRESHOLD = time(6, 0)  # Jobs before 6 AM = no check marks

# Morning referral order by classification (Rule 2)
REFERRAL_ORDER = {
    BookClassification.INSIDE_WIREPERSON: time(8, 30),
    BookClassification.SOUND_COMM: time(9, 0),
    BookClassification.MARINE: time(9, 0),
    BookClassification.STOCKPERSON: time(9, 0),
    BookClassification.LIGHT_FIXTURE: time(9, 0),
    BookClassification.RESIDENTIAL: time(9, 0),
    BookClassification.TRADESHOW: time(9, 30),
    BookClassification.TECHNICIAN: time(9, 0),
    BookClassification.UTILITY_WORKER: time(9, 0),
    BookClassification.TERO_APPRENTICE: time(9, 0),
}


# --- Create & Update Operations ---


def create_request(
    db: Session,
    *,
    employer_id: int,
    book_id: int,
    workers_requested: int,
    start_date: date,
    created_by_id: int,
    worksite_name: Optional[str] = None,
    worksite_address: Optional[str] = None,
    city: Optional[str] = None,
    start_time: Optional[time] = None,
    estimated_duration_days: Optional[int] = None,
    is_short_call: Optional[bool] = None,
    short_call_days: Optional[int] = None,
    is_foreperson_by_name: bool = False,
    foreperson_member_id: Optional[int] = None,
    requirements: Optional[str] = None,
    comments: Optional[str] = None,
    agreement_type: Optional[AgreementType] = None,
    allows_online_bidding: bool = True,
) -> LaborRequest:
    """
    Create a new labor request from an employer.

    Business Rules:
    - Rule 3: Requests must be received by 3:00 PM for next-morning referral
    - Rule 11: Pre-calculates generates_check_mark flag
    - Sets up bidding window times if online bidding is enabled

    Raises:
        ValueError: If employer or book not found
    """
    # Validate employer
    employer = db.query(Organization).filter(Organization.id == employer_id).first()
    if not employer:
        raise ValueError("Employer not found")

    # Validate book
    book = referral_book_service.get_by_id(db, book_id)
    if not book:
        raise ValueError("Referral book not found")
    if not book.is_active:
        raise ValueError("Referral book is not active")

    # Auto-detect short call
    if is_short_call is None and estimated_duration_days is not None:
        is_short_call = estimated_duration_days <= 10

    if is_short_call and short_call_days is None:
        short_call_days = estimated_duration_days

    # Generate request number
    request_number = _generate_request_number(db)

    # Determine check mark status (Rule 11)
    generates_check_mark, no_check_reason = _determine_check_mark(
        is_short_call=is_short_call or False,
        start_time=start_time,
        requirements=requirements,
        agreement_type=agreement_type,
    )

    # Set up bidding window
    bidding_opens_at = None
    bidding_closes_at = None
    if allows_online_bidding and book.internet_bidding_enabled:
        # Bidding opens at 5:30 PM the day before start
        day_before = start_date - timedelta(days=1)
        bidding_opens_at = datetime.combine(day_before, BIDDING_OPEN)
        bidding_closes_at = datetime.combine(start_date, BIDDING_CLOSE)

    request = LaborRequest(
        employer_id=employer_id,
        employer_name=employer.name,
        book_id=book_id,
        classification=book.classification,
        region=book.region,
        contract_code=book.contract_code,
        request_number=request_number,
        request_date=datetime.utcnow(),
        workers_requested=workers_requested,
        workers_dispatched=0,
        worksite_name=worksite_name,
        worksite_address=worksite_address,
        city=city,
        start_date=start_date,
        start_time=start_time,
        estimated_duration_days=estimated_duration_days,
        is_short_call=is_short_call or False,
        short_call_days=short_call_days,
        is_foreperson_by_name=is_foreperson_by_name,
        foreperson_member_id=foreperson_member_id,
        generates_check_mark=generates_check_mark,
        no_check_mark_reason=no_check_reason,
        agreement_type=agreement_type,
        requirements=requirements,
        comments=comments,
        status=LaborRequestStatus.OPEN,
        allows_online_bidding=allows_online_bidding and book.internet_bidding_enabled,
        bidding_opens_at=bidding_opens_at,
        bidding_closes_at=bidding_closes_at,
        created_by_id=created_by_id,
    )

    db.add(request)
    db.commit()
    db.refresh(request)

    return request


def update_request(
    db: Session,
    request_id: int,
    **kwargs,
) -> LaborRequest:
    """
    Update a labor request.

    Only OPEN requests can be modified.

    Raises:
        ValueError: Request not found or not in OPEN status
    """
    request = get_by_id(db, request_id)
    if not request:
        raise ValueError("Labor request not found")

    if request.status != LaborRequestStatus.OPEN:
        raise ValueError(f"Cannot update request: status is {request.status.value}")

    for field, value in kwargs.items():
        if hasattr(request, field) and value is not None:
            setattr(request, field, value)

    # Recalculate check mark if relevant fields changed
    if any(k in kwargs for k in ["is_short_call", "start_time", "requirements", "agreement_type"]):
        generates, reason = _determine_check_mark(
            is_short_call=request.is_short_call,
            start_time=request.start_time,
            requirements=request.requirements,
            agreement_type=request.agreement_type,
        )
        request.generates_check_mark = generates
        request.no_check_mark_reason = reason

    db.commit()
    db.refresh(request)
    return request


# --- Status Transitions ---


def cancel_request(
    db: Session,
    request_id: int,
    reason: Optional[str] = None,
) -> LaborRequest:
    """
    Cancel an unfilled labor request.

    Only OPEN or PARTIALLY_FILLED requests can be cancelled.

    Raises:
        ValueError: Request not found or already filled/expired
    """
    request = get_by_id(db, request_id)
    if not request:
        raise ValueError("Labor request not found")

    if request.status not in (LaborRequestStatus.OPEN, LaborRequestStatus.PARTIALLY_FILLED):
        raise ValueError(f"Cannot cancel request: status is {request.status.value}")

    request.status = LaborRequestStatus.CANCELLED
    request.comments = f"{request.comments or ''}\nCancelled: {reason or 'No reason given'}".strip()

    db.commit()
    db.refresh(request)
    return request


def expire_request(db: Session, request_id: int) -> LaborRequest:
    """
    Mark an unfilled request as expired.

    Called by end-of-day batch processing.

    Raises:
        ValueError: Request not found
    """
    request = get_by_id(db, request_id)
    if not request:
        raise ValueError("Labor request not found")

    if request.status not in (LaborRequestStatus.OPEN, LaborRequestStatus.PARTIALLY_FILLED):
        raise ValueError(f"Cannot expire request: status is {request.status.value}")

    request.status = LaborRequestStatus.EXPIRED

    db.commit()
    db.refresh(request)
    return request


def fill_request(db: Session, request_id: int) -> LaborRequest:
    """
    Mark a request as filled (all workers dispatched).

    Raises:
        ValueError: Request not found
    """
    request = get_by_id(db, request_id)
    if not request:
        raise ValueError("Labor request not found")

    request.status = LaborRequestStatus.FILLED

    db.commit()
    db.refresh(request)
    return request


def increment_dispatched(db: Session, request_id: int) -> LaborRequest:
    """
    Increment workers_dispatched count.

    Automatically updates status to PARTIALLY_FILLED or FILLED.
    """
    request = get_by_id(db, request_id)
    if not request:
        raise ValueError("Labor request not found")

    request.workers_dispatched += 1

    if request.workers_dispatched >= request.workers_requested:
        request.status = LaborRequestStatus.FILLED
    elif request.workers_dispatched > 0:
        request.status = LaborRequestStatus.PARTIALLY_FILLED

    db.commit()
    db.refresh(request)
    return request


# --- Query Methods ---


def get_by_id(db: Session, request_id: int) -> Optional[LaborRequest]:
    """Get a labor request by ID."""
    return db.query(LaborRequest).filter(LaborRequest.id == request_id).first()


def get_open_requests(
    db: Session,
    *,
    book_id: Optional[int] = None,
    classification: Optional[BookClassification] = None,
    region: Optional[BookRegion] = None,
    employer_id: Optional[int] = None,
) -> list[LaborRequest]:
    """Get all unfilled labor requests with optional filters."""
    query = db.query(LaborRequest).filter(
        LaborRequest.status.in_([LaborRequestStatus.OPEN, LaborRequestStatus.PARTIALLY_FILLED])
    )

    if book_id:
        query = query.filter(LaborRequest.book_id == book_id)
    if classification:
        query = query.filter(LaborRequest.classification == classification)
    if region:
        query = query.filter(LaborRequest.region == region)
    if employer_id:
        query = query.filter(LaborRequest.employer_id == employer_id)

    return query.order_by(LaborRequest.request_date.asc()).all()


def get_requests_for_book(db: Session, book_id: int) -> list[LaborRequest]:
    """Get all requests targeting a specific book."""
    return (
        db.query(LaborRequest)
        .filter(
            LaborRequest.book_id == book_id,
            LaborRequest.status.in_([LaborRequestStatus.OPEN, LaborRequestStatus.PARTIALLY_FILLED]),
        )
        .order_by(LaborRequest.request_date.asc())
        .all()
    )


def get_employer_requests(
    db: Session,
    employer_id: int,
    include_filled: bool = False,
    limit: int = 50,
) -> list[LaborRequest]:
    """Get request history for an employer."""
    query = db.query(LaborRequest).filter(LaborRequest.employer_id == employer_id)

    if not include_filled:
        query = query.filter(
            LaborRequest.status.in_([LaborRequestStatus.OPEN, LaborRequestStatus.PARTIALLY_FILLED])
        )

    return query.order_by(LaborRequest.request_date.desc()).limit(limit).all()


def get_requests_for_morning(
    db: Session,
    target_date: Optional[date] = None,
) -> list[LaborRequest]:
    """
    Get all requests ready for morning referral, ordered by classification time.

    Rule 2: Wire 8:30 AM → S&C/Marine/Stock/LFM/Residential 9:00 AM → Tradeshow 9:30 AM

    Returns requests ordered by their classification's referral time.
    """
    if target_date is None:
        target_date = date.today()

    requests = (
        db.query(LaborRequest)
        .filter(
            LaborRequest.status.in_([LaborRequestStatus.OPEN, LaborRequestStatus.PARTIALLY_FILLED]),
            LaborRequest.start_date == target_date,
        )
        .all()
    )

    # Sort by classification referral time
    def get_referral_time(req: LaborRequest) -> time:
        if req.classification:
            return REFERRAL_ORDER.get(req.classification, time(9, 0))
        return time(9, 0)

    return sorted(requests, key=get_referral_time)


# --- Check Mark Determination (Rule 11) ---


def _determine_check_mark(
    *,
    is_short_call: bool,
    start_time: Optional[time],
    requirements: Optional[str],
    agreement_type: Optional[AgreementType],
) -> Tuple[bool, Optional[NoCheckMarkReason]]:
    """
    Pre-calculate whether a request generates check marks (Rule 11).

    Returns False for:
    - Specialty skills not in CBA
    - MOU sites
    - Start times before 6:00 AM
    - Under scale work recovery
    - Short call requests
    - Employer rejection (handled separately)
    """
    # Short call = no check mark
    if is_short_call:
        return False, NoCheckMarkReason.SHORT_CALL

    # Early start (before 6 AM) = no check mark
    if start_time and start_time < EARLY_START_THRESHOLD:
        return False, NoCheckMarkReason.EARLY_START

    # Check requirements for specialty indicators
    if requirements:
        requirements_lower = requirements.lower()
        if any(kw in requirements_lower for kw in ["specialty", "specialized", "special skill"]):
            return False, NoCheckMarkReason.SPECIALTY
        if any(kw in requirements_lower for kw in ["mou", "memorandum of understanding"]):
            return False, NoCheckMarkReason.MOU_JOBSITE
        if any(kw in requirements_lower for kw in ["under scale", "below scale", "market recovery"]):
            return False, NoCheckMarkReason.UNDER_SCALE

    # Normal request generates check marks
    return True, None


def determine_check_mark(request: LaborRequest) -> Tuple[bool, Optional[NoCheckMarkReason]]:
    """
    Public wrapper for check mark determination.

    Returns (generates_check_mark, reason_if_not).
    """
    return _determine_check_mark(
        is_short_call=request.is_short_call,
        start_time=request.start_time,
        requirements=request.requirements,
        agreement_type=request.agreement_type,
    )


# --- Bidding Window Validation (Rule 8) ---


def validate_bidding_window(request: LaborRequest) -> bool:
    """
    Check if current time is within the online bidding window.

    Rule 8: Bidding window is 5:30 PM to 7:00 AM.
    """
    if not request.allows_online_bidding:
        return False

    now = datetime.utcnow()

    if request.bidding_opens_at and request.bidding_closes_at:
        return request.bidding_opens_at <= now <= request.bidding_closes_at

    # Fallback to time-based check
    current_time = now.time()
    # Window spans midnight: 5:30 PM to 7:00 AM
    return current_time >= BIDDING_OPEN or current_time <= BIDDING_CLOSE


def is_bidding_open(db: Session, request_id: int) -> bool:
    """Check if bidding is currently open for a request."""
    request = get_by_id(db, request_id)
    if not request:
        return False
    return validate_bidding_window(request)


# --- Cutoff Validation (Rule 3) ---


def is_past_cutoff_for_tomorrow() -> bool:
    """
    Check if current time is past the 3 PM cutoff for next-morning referral.

    Rule 3: Requests received after 3:00 PM go to the following day.
    """
    return datetime.utcnow().time() >= MORNING_CUTOFF


def get_effective_start_date(requested_date: date) -> date:
    """
    Get the effective start date accounting for cutoff.

    If it's past 3 PM and the requested date is tomorrow,
    the effective date becomes the day after.
    """
    today = date.today()
    tomorrow = today + timedelta(days=1)

    if requested_date <= tomorrow and is_past_cutoff_for_tomorrow():
        return tomorrow + timedelta(days=1)

    return requested_date


# --- Batch Processing ---


def expire_old_requests(db: Session) -> list[LaborRequest]:
    """
    Batch process: expire all unfilled requests past their start date.

    Called by daily enforcement job.
    """
    today = date.today()
    expired = []

    old_requests = (
        db.query(LaborRequest)
        .filter(
            LaborRequest.status.in_([LaborRequestStatus.OPEN, LaborRequestStatus.PARTIALLY_FILLED]),
            LaborRequest.start_date < today,
        )
        .all()
    )

    for request in old_requests:
        request.status = LaborRequestStatus.EXPIRED
        expired.append(request)

    if expired:
        db.commit()

    return expired


# --- Internal Helpers ---


def _generate_request_number(db: Session) -> str:
    """Generate a unique request number."""
    today = date.today()
    prefix = today.strftime("REQ%Y%m%d")

    # Count today's requests
    count = (
        db.query(func.count(LaborRequest.id))
        .filter(LaborRequest.request_number.like(f"{prefix}%"))
        .scalar()
        or 0
    )

    return f"{prefix}-{count + 1:04d}"
