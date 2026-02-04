"""
Service for job bid operations.

Created: February 4, 2026 (Week 23 Session B)
Phase 7 - Referral & Dispatch System

Manages the online/email bidding workflow - Rule 8 implementation.
Tracks bids, rejections, and bidding privilege suspensions.
"""
from typing import Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from src.db.enums import (
    BidStatus,
    LaborRequestStatus,
    RegistrationStatus,
    RolloffReason,
)
from src.models.job_bid import JobBid
from src.models.labor_request import LaborRequest
from src.models.book_registration import BookRegistration
from src.models.member import Member
from src.services import labor_request_service
from src.services import book_registration_service


# --- Constants (per Local 46 Rules) ---
REJECTION_WINDOW_MONTHS = 12      # Track rejections over 12 months
SUSPENSION_DURATION_MONTHS = 12  # 1-year bidding suspension
MAX_REJECTIONS_BEFORE_SUSPENSION = 2  # 2nd rejection = suspension


# --- Bid Operations ---


def place_bid(
    db: Session,
    *,
    member_id: int,
    labor_request_id: int,
    registration_id: int,
    bid_method: str = "online",
) -> JobBid:
    """
    Place a bid on a labor request.

    Business Rules:
    - Rule 8: Only valid during bidding window (5:30 PM – 7:00 AM)
    - Member must have active registration on the relevant book
    - Member must not be suspended from bidding
    - Member cannot bid on same request twice

    Raises:
        ValueError: Invalid bid conditions
    """
    # Validate labor request
    request = labor_request_service.get_by_id(db, labor_request_id)
    if not request:
        raise ValueError("Labor request not found")

    if request.status not in (LaborRequestStatus.OPEN, LaborRequestStatus.PARTIALLY_FILLED):
        raise ValueError(f"Cannot bid on request: status is {request.status.value}")

    # Validate bidding window
    if not labor_request_service.validate_bidding_window(request):
        raise ValueError("Bidding is not currently open for this request")

    # Validate registration
    registration = book_registration_service.get_by_id(db, registration_id)
    if not registration:
        raise ValueError("Registration not found")

    if registration.member_id != member_id:
        raise ValueError("Registration does not belong to this member")

    if registration.status != RegistrationStatus.REGISTERED:
        raise ValueError(f"Cannot bid: registration status is {registration.status.value}")

    # Check for existing bid
    existing_bid = (
        db.query(JobBid)
        .filter(
            JobBid.labor_request_id == labor_request_id,
            JobBid.member_id == member_id,
            JobBid.bid_status.in_([BidStatus.PENDING, BidStatus.ACCEPTED]),
        )
        .first()
    )
    if existing_bid:
        raise ValueError("Member has already bid on this request")

    # Check bidding suspension
    suspension_status = check_suspension_status(db, member_id)
    if suspension_status["is_suspended"]:
        raise ValueError(
            f"Bidding privileges suspended until {suspension_status['suspended_until']}"
        )

    # Get queue position
    position = book_registration_service.get_member_position(db, registration_id)

    bid = JobBid(
        labor_request_id=labor_request_id,
        member_id=member_id,
        registration_id=registration_id,
        bid_submitted_at=datetime.utcnow(),
        bid_method=bid_method,
        queue_position_at_bid=position,
        bid_status=BidStatus.PENDING,
    )

    db.add(bid)
    db.commit()
    db.refresh(bid)

    return bid


def withdraw_bid(
    db: Session,
    bid_id: int,
    reason: Optional[str] = None,
) -> JobBid:
    """
    Withdraw a pending bid.

    Only PENDING bids can be withdrawn.

    Raises:
        ValueError: Bid not found or not pending
    """
    bid = get_by_id(db, bid_id)
    if not bid:
        raise ValueError("Bid not found")

    if bid.bid_status != BidStatus.PENDING:
        raise ValueError(f"Cannot withdraw bid: status is {bid.bid_status.value}")

    bid.bid_status = BidStatus.WITHDRAWN
    bid.notes = reason

    db.commit()
    db.refresh(bid)

    return bid


def accept_bid(
    db: Session,
    bid_id: int,
    processed_by_id: int,
) -> JobBid:
    """
    Accept a bid (staff action).

    Changes bid status to ACCEPTED. The dispatch is created separately.

    Raises:
        ValueError: Bid not found or not pending
    """
    bid = get_by_id(db, bid_id)
    if not bid:
        raise ValueError("Bid not found")

    if bid.bid_status != BidStatus.PENDING:
        raise ValueError(f"Cannot accept bid: status is {bid.bid_status.value}")

    bid.bid_status = BidStatus.ACCEPTED
    bid.processed_at = datetime.utcnow()
    bid.processed_by_id = processed_by_id

    db.commit()
    db.refresh(bid)

    return bid


def reject_bid(
    db: Session,
    bid_id: int,
    reason: Optional[str] = None,
) -> JobBid:
    """
    Member rejects an accepted bid. This counts as a quit (Rule 8/12).

    Business Rules:
    - First rejection in 12 months: warning, counts as quit
    - Second rejection in 12 months: bidding privileges revoked for 1 year

    Raises:
        ValueError: Bid not found or not in correct status
    """
    bid = get_by_id(db, bid_id)
    if not bid:
        raise ValueError("Bid not found")

    if bid.bid_status != BidStatus.ACCEPTED:
        raise ValueError(
            f"Can only reject accepted bids (current status: {bid.bid_status.value})"
        )

    # Mark as rejected
    bid.bid_status = BidStatus.REJECTED
    bid.rejected_by_member = True
    bid.rejection_reason = reason
    bid.rejection_date = datetime.utcnow()

    # Count rejections in the last 12 months
    rejection_count = count_rejections_in_window(db, bid.member_id)
    new_rejection_count = rejection_count + 1

    # Check if this triggers suspension
    if new_rejection_count >= MAX_REJECTIONS_BEFORE_SUSPENSION:
        # Apply 1-year bidding suspension
        apply_bidding_suspension(db, bid.member_id, reason="Second bid rejection in 12 months")
        bid.notes = f"SUSPENSION APPLIED: 2nd rejection in 12 months. Bidding privileges revoked for 1 year."
    else:
        bid.notes = f"Warning: {new_rejection_count}/{MAX_REJECTIONS_BEFORE_SUSPENSION} rejections in 12 months. Next rejection will result in 1-year suspension."

    db.commit()
    db.refresh(bid)

    return bid


def mark_not_selected(
    db: Session,
    bid_id: int,
) -> JobBid:
    """
    Mark a bid as not selected (higher-priority member was dispatched instead).

    Raises:
        ValueError: Bid not found
    """
    bid = get_by_id(db, bid_id)
    if not bid:
        raise ValueError("Bid not found")

    if bid.bid_status != BidStatus.PENDING:
        raise ValueError(f"Cannot mark as not selected: status is {bid.bid_status.value}")

    bid.bid_status = BidStatus.REJECTED
    bid.rejection_reason = "Higher-priority member selected"
    bid.processed_at = datetime.utcnow()

    db.commit()
    db.refresh(bid)

    return bid


# --- Process Bids for Request ---


def process_bids(
    db: Session,
    labor_request_id: int,
    processed_by_id: int,
) -> list[JobBid]:
    """
    Process all pending bids for a request in FIFO order (by APN).

    For each slot to fill:
    1. Find highest-priority pending bid (lowest APN)
    2. Mark bid as ACCEPTED
    3. Remaining bids marked as NOT_SELECTED when request is filled

    Returns list of accepted bids.
    """
    request = labor_request_service.get_by_id(db, labor_request_id)
    if not request:
        raise ValueError("Labor request not found")

    # Get all pending bids, ordered by queue position (FIFO)
    pending_bids = (
        db.query(JobBid)
        .filter(
            JobBid.labor_request_id == labor_request_id,
            JobBid.bid_status == BidStatus.PENDING,
        )
        .order_by(JobBid.queue_position_at_bid.asc())
        .all()
    )

    if not pending_bids:
        return []

    slots_remaining = request.workers_remaining
    accepted_bids = []

    for bid in pending_bids:
        if slots_remaining <= 0:
            # Request is filled, mark remaining as not selected
            bid.bid_status = BidStatus.REJECTED
            bid.rejection_reason = "Request filled by higher-priority members"
            bid.processed_at = datetime.utcnow()
            bid.processed_by_id = processed_by_id
        else:
            # Accept this bid
            bid.bid_status = BidStatus.ACCEPTED
            bid.processed_at = datetime.utcnow()
            bid.processed_by_id = processed_by_id
            accepted_bids.append(bid)
            slots_remaining -= 1

    db.commit()

    return accepted_bids


# --- Query Methods ---


def get_by_id(db: Session, bid_id: int) -> Optional[JobBid]:
    """Get a bid by ID."""
    return db.query(JobBid).filter(JobBid.id == bid_id).first()


def get_bids_for_request(
    db: Session,
    labor_request_id: int,
    status: Optional[BidStatus] = None,
) -> list[JobBid]:
    """Get all bids for a labor request."""
    query = db.query(JobBid).filter(JobBid.labor_request_id == labor_request_id)

    if status:
        query = query.filter(JobBid.bid_status == status)

    return query.order_by(JobBid.queue_position_at_bid.asc()).all()


def get_member_bid_history(
    db: Session,
    member_id: int,
    limit: int = 50,
    include_all: bool = False,
) -> list[JobBid]:
    """Get bid history for a member."""
    query = db.query(JobBid).filter(JobBid.member_id == member_id)

    if not include_all:
        # Only recent bids
        cutoff = datetime.utcnow() - timedelta(days=365)
        query = query.filter(JobBid.bid_submitted_at >= cutoff)

    return query.order_by(JobBid.bid_submitted_at.desc()).limit(limit).all()


def get_pending_bids_for_member(
    db: Session,
    member_id: int,
) -> list[JobBid]:
    """Get all pending bids for a member."""
    return (
        db.query(JobBid)
        .filter(
            JobBid.member_id == member_id,
            JobBid.bid_status == BidStatus.PENDING,
        )
        .order_by(JobBid.bid_submitted_at.desc())
        .all()
    )


# --- Suspension Management ---


def check_suspension_status(db: Session, member_id: int) -> dict:
    """
    Check if member has active bidding suspension.

    Returns:
    {
        'is_suspended': bool,
        'suspended_until': datetime | None,
        'rejections_in_window': int,
        'next_rejection_causes_suspension': bool
    }
    """
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return {
            "is_suspended": False,
            "suspended_until": None,
            "rejections_in_window": 0,
            "next_rejection_causes_suspension": False,
        }

    # Check for active suspension (stored on member or in separate table)
    # For now, we check by looking at recent rejections
    is_suspended = False
    suspended_until = None

    # Check if there was a suspension-causing rejection
    suspension_check = (
        db.query(JobBid)
        .filter(
            JobBid.member_id == member_id,
            JobBid.rejected_by_member == True,
            JobBid.notes.ilike("%SUSPENSION APPLIED%"),
            JobBid.rejection_date >= datetime.utcnow() - timedelta(days=365),
        )
        .order_by(JobBid.rejection_date.desc())
        .first()
    )

    if suspension_check:
        suspended_until = suspension_check.rejection_date + timedelta(days=365)
        if datetime.utcnow() < suspended_until:
            is_suspended = True

    rejections_in_window = count_rejections_in_window(db, member_id)

    return {
        "is_suspended": is_suspended,
        "suspended_until": suspended_until,
        "rejections_in_window": rejections_in_window,
        "next_rejection_causes_suspension": rejections_in_window >= 1,
    }


def count_rejections_in_window(db: Session, member_id: int) -> int:
    """Count member's bid rejections in the last 12 months."""
    window_start = datetime.utcnow() - timedelta(days=365)

    return (
        db.query(func.count(JobBid.id))
        .filter(
            JobBid.member_id == member_id,
            JobBid.rejected_by_member == True,
            JobBid.rejection_date >= window_start,
        )
        .scalar()
        or 0
    )


def apply_bidding_suspension(
    db: Session,
    member_id: int,
    reason: str,
) -> None:
    """
    Apply a 1-year bidding suspension to a member.

    Per Rule 8: Second rejection in 12 months = lose internet privileges for 1 year.
    """
    # The suspension is tracked via the rejection record with SUSPENSION APPLIED note
    # In a full implementation, we might have a separate bidding_suspensions table
    pass


def revoke_bidding_suspension(
    db: Session,
    member_id: int,
    reason: str,
) -> None:
    """
    Early revoke a bidding suspension (admin action).
    """
    # Would update the suspension record to ended status
    pass


# --- Batch Processing ---


def expire_old_bids(db: Session) -> list[JobBid]:
    """
    Expire bids on requests that are no longer accepting bids.

    Called by daily enforcement job.
    """
    expired = []

    # Find pending bids on non-open requests
    old_bids = (
        db.query(JobBid)
        .join(LaborRequest)
        .filter(
            JobBid.bid_status == BidStatus.PENDING,
            LaborRequest.status.not_in([LaborRequestStatus.OPEN, LaborRequestStatus.PARTIALLY_FILLED]),
        )
        .all()
    )

    for bid in old_bids:
        bid.bid_status = BidStatus.EXPIRED
        expired.append(bid)

    if expired:
        db.commit()

    return expired
