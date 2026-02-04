"""
Service for book registration operations.

Created: February 4, 2026 (Week 22 Session B/C)
Phase 7 - Referral & Dispatch System

Enforces referral rules: registration, re-sign, status transitions,
queue positioning, check marks, and roll-off rules.
"""
from typing import Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from src.db.enums import (
    RegistrationStatus,
    RegistrationAction,
    ExemptReason,
    RolloffReason,
    NoCheckMarkReason,
)
from src.models.referral_book import ReferralBook
from src.models.book_registration import BookRegistration
from src.models.registration_activity import RegistrationActivity
from src.models.member import Member
from src.services import referral_book_service


# --- Registration Operations ---


def register_member(
    db: Session,
    member_id: int,
    book_id: int,
    performed_by_id: int,
    registration_method: str = "in_person",
    notes: Optional[str] = None,
) -> BookRegistration:
    """
    Register a member on a referral book.

    Business Rules:
    - Member must not already be REGISTERED on this book
    - Member CAN be registered on multiple different books simultaneously
    - Assigns next APN (registration_number) in sequence
    - Sets status = REGISTERED, has_check_mark = True
    - Creates RegistrationActivity record

    Raises:
        ValueError: Member already registered, book not active, or member not found
    """
    # Validate eligibility
    can_reg, reason = can_register(db, member_id, book_id)
    if not can_reg:
        raise ValueError(reason)

    # Get next APN
    apn = get_next_apn(db, book_id)

    # Create registration
    now = datetime.utcnow()
    book = referral_book_service.get_by_id(db, book_id)
    re_sign_deadline = now + timedelta(days=book.re_sign_days) if book.re_sign_days else None

    registration = BookRegistration(
        member_id=member_id,
        book_id=book_id,
        registration_number=apn,
        registration_date=now,
        registration_method=registration_method,
        status=RegistrationStatus.REGISTERED,
        has_check_mark=True,
        check_marks=0,
        consecutive_missed_check_marks=0,
        last_re_sign_date=now,
        re_sign_deadline=re_sign_deadline,
        notes=notes,
    )
    db.add(registration)
    db.flush()  # Get ID for activity

    # Create activity record
    activity = RegistrationActivity(
        registration_id=registration.id,
        member_id=member_id,
        book_id=book_id,
        action=RegistrationAction.REGISTER,
        new_status=RegistrationStatus.REGISTERED,
        new_position=_get_queue_position(db, book_id, apn),
        performed_by_id=performed_by_id,
        processor="SYSTEM",
        details=f"Initial registration on {book.name}",
    )
    db.add(activity)
    db.commit()
    db.refresh(registration)

    return registration


def get_next_apn(db: Session, book_id: int) -> Decimal:
    """
    Calculate the next APN (registration number) for a book.

    APNs are DECIMAL(10,2). New registrations get the next whole number.
    """
    max_apn = (
        db.query(func.max(BookRegistration.registration_number))
        .filter(BookRegistration.book_id == book_id)
        .scalar()
    )

    if max_apn is None:
        return Decimal("1.00")

    # Get next whole number
    next_whole = int(max_apn) + 1
    return Decimal(f"{next_whole}.00")


def re_sign_member(
    db: Session,
    registration_id: int,
    performed_by_id: int,
    notes: Optional[str] = None,
) -> BookRegistration:
    """
    Re-sign a member on their book (extend registration).

    Business Rules:
    - Member must currently be REGISTERED on the book
    - Re-sign resets the roll-off countdown
    - Updates re_sign_date to now
    - Creates RegistrationActivity record

    Raises:
        ValueError: Registration not found or not in REGISTERED status
    """
    registration = get_by_id(db, registration_id)
    if not registration:
        raise ValueError("Registration not found")

    if registration.status != RegistrationStatus.REGISTERED:
        raise ValueError(
            f"Cannot re-sign: registration status is {registration.status.value}"
        )

    # Check if past grace period
    can_resign, reason = can_re_sign(db, registration_id)
    if not can_resign:
        raise ValueError(reason)

    now = datetime.utcnow()
    book = registration.book

    old_deadline = registration.re_sign_deadline
    registration.last_re_sign_date = now
    registration.re_sign_deadline = (
        now + timedelta(days=book.re_sign_days) if book.re_sign_days else None
    )

    # Create activity
    activity = RegistrationActivity(
        registration_id=registration_id,
        member_id=registration.member_id,
        book_id=registration.book_id,
        action=RegistrationAction.RE_SIGN,
        previous_status=RegistrationStatus.REGISTERED,
        new_status=RegistrationStatus.REGISTERED,
        performed_by_id=performed_by_id,
        details=f"Re-signed. New deadline: {registration.re_sign_deadline}",
        notes=notes,
    )
    db.add(activity)
    db.commit()
    db.refresh(registration)

    return registration


# --- Status Transitions ---


def resign_member(
    db: Session,
    registration_id: int,
    performed_by_id: int,
    reason: Optional[str] = None,
) -> BookRegistration:
    """
    Member voluntarily resigns from a book.

    Business Rules:
    - Sets status = RESIGNED
    - Creates RegistrationActivity record
    - Does NOT affect registrations on other books
    """
    registration = get_by_id(db, registration_id)
    if not registration:
        raise ValueError("Registration not found")

    if registration.status != RegistrationStatus.REGISTERED:
        raise ValueError(
            f"Cannot resign: registration status is {registration.status.value}"
        )

    old_status = registration.status
    registration.status = RegistrationStatus.RESIGNED

    activity = RegistrationActivity(
        registration_id=registration_id,
        member_id=registration.member_id,
        book_id=registration.book_id,
        action=RegistrationAction.RESIGN,
        previous_status=old_status,
        new_status=RegistrationStatus.RESIGNED,
        performed_by_id=performed_by_id,
        reason=reason,
        details="Member voluntarily resigned from book",
    )
    db.add(activity)
    db.commit()
    db.refresh(registration)

    return registration


def roll_off_member(
    db: Session,
    registration_id: int,
    performed_by_id: int,
    reason: RolloffReason = RolloffReason.EXPIRED,
    notes: Optional[str] = None,
) -> BookRegistration:
    """
    Roll a member off a book (involuntary removal).

    Business Rules:
    - Sets status = ROLLED_OFF
    - Sets roll_off_date to now
    - Creates RegistrationActivity record
    """
    registration = get_by_id(db, registration_id)
    if not registration:
        raise ValueError("Registration not found")

    if registration.status != RegistrationStatus.REGISTERED:
        raise ValueError(
            f"Cannot roll off: registration status is {registration.status.value}"
        )

    old_status = registration.status
    registration.status = RegistrationStatus.ROLLED_OFF
    registration.roll_off_date = datetime.utcnow()
    registration.roll_off_reason = reason

    activity = RegistrationActivity(
        registration_id=registration_id,
        member_id=registration.member_id,
        book_id=registration.book_id,
        action=RegistrationAction.ROLL_OFF,
        previous_status=old_status,
        new_status=RegistrationStatus.ROLLED_OFF,
        performed_by_id=performed_by_id,
        reason=reason.value,
        notes=notes,
        details=f"Rolled off: {reason.value}",
    )
    db.add(activity)
    db.commit()
    db.refresh(registration)

    return registration


def mark_dispatched(
    db: Session,
    registration_id: int,
    dispatch_id: int,
    performed_by_id: int,
) -> BookRegistration:
    """
    Mark a registration as dispatched (member accepted a job).

    Business Rules:
    - Sets status = DISPATCHED
    - Links to the Dispatch record
    - Creates RegistrationActivity record
    """
    registration = get_by_id(db, registration_id)
    if not registration:
        raise ValueError("Registration not found")

    if registration.status != RegistrationStatus.REGISTERED:
        raise ValueError(
            f"Cannot dispatch: registration status is {registration.status.value}"
        )

    old_status = registration.status
    old_position = _get_queue_position(
        db, registration.book_id, registration.registration_number
    )

    registration.status = RegistrationStatus.DISPATCHED

    activity = RegistrationActivity(
        registration_id=registration_id,
        member_id=registration.member_id,
        book_id=registration.book_id,
        action=RegistrationAction.DISPATCH,
        previous_status=old_status,
        new_status=RegistrationStatus.DISPATCHED,
        previous_position=old_position,
        performed_by_id=performed_by_id,
        dispatch_id=dispatch_id,
        details="Dispatched to job",
    )
    db.add(activity)
    db.commit()
    db.refresh(registration)

    return registration


# --- Query Methods ---


def get_by_id(db: Session, registration_id: int) -> Optional[BookRegistration]:
    """Get a registration by ID."""
    return (
        db.query(BookRegistration)
        .filter(BookRegistration.id == registration_id)
        .first()
    )


def get_book_queue(
    db: Session,
    book_id: int,
    status: Optional[RegistrationStatus] = None,
    include_exempt: bool = True,
) -> list[BookRegistration]:
    """
    Get the ordered queue for a book.

    Ordering: by registration_number (APN) ascending.
    This is FIFO - lowest APN = longest waiting = first dispatched.
    """
    query = db.query(BookRegistration).filter(BookRegistration.book_id == book_id)

    if status:
        query = query.filter(BookRegistration.status == status)
    else:
        # Default to REGISTERED status
        query = query.filter(BookRegistration.status == RegistrationStatus.REGISTERED)

    if not include_exempt:
        query = query.filter(BookRegistration.is_exempt == False)

    return query.order_by(BookRegistration.registration_number.asc()).all()


def get_member_registrations(
    db: Session,
    member_id: int,
    active_only: bool = True,
) -> list[BookRegistration]:
    """Get all registrations for a member."""
    query = db.query(BookRegistration).filter(BookRegistration.member_id == member_id)

    if active_only:
        query = query.filter(BookRegistration.status == RegistrationStatus.REGISTERED)

    return query.order_by(BookRegistration.registration_date.desc()).all()


def get_member_position(db: Session, registration_id: int) -> Optional[int]:
    """
    Get a member's current position in the book queue.

    Position 1 = next to be dispatched.
    Returns None if not in REGISTERED status.
    """
    registration = get_by_id(db, registration_id)
    if not registration or registration.status != RegistrationStatus.REGISTERED:
        return None

    return _get_queue_position(
        db, registration.book_id, registration.registration_number
    )


def get_registrations_expiring_soon(
    db: Session,
    days_threshold: int = 7,
) -> list[BookRegistration]:
    """
    Get registrations approaching their roll-off date.

    Used by the re-sign reminder system.
    """
    threshold = datetime.utcnow() + timedelta(days=days_threshold)

    return (
        db.query(BookRegistration)
        .filter(
            BookRegistration.status == RegistrationStatus.REGISTERED,
            BookRegistration.is_exempt == False,
            BookRegistration.re_sign_deadline.isnot(None),
            BookRegistration.re_sign_deadline <= threshold,
        )
        .order_by(BookRegistration.re_sign_deadline.asc())
        .all()
    )


# --- Validation Helpers ---


def can_register(
    db: Session, member_id: int, book_id: int
) -> Tuple[bool, Optional[str]]:
    """
    Check if a member can register on a book.

    Returns (True, None) or (False, reason_string).
    """
    # Check book exists and is active
    book = referral_book_service.get_by_id(db, book_id)
    if not book:
        return False, "Book not found"
    if not book.is_active:
        return False, "Book is not active"

    # Check member exists
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return False, "Member not found"

    # Check not already registered
    existing = (
        db.query(BookRegistration)
        .filter(
            BookRegistration.member_id == member_id,
            BookRegistration.book_id == book_id,
            BookRegistration.status.in_(
                [RegistrationStatus.REGISTERED, RegistrationStatus.DISPATCHED]
            ),
        )
        .first()
    )
    if existing:
        return False, f"Member already has active registration on this book (status: {existing.status.value})"

    return True, None


def can_re_sign(db: Session, registration_id: int) -> Tuple[bool, Optional[str]]:
    """
    Check if a registration can be re-signed.

    Returns (True, None) or (False, reason_string).
    """
    registration = get_by_id(db, registration_id)
    if not registration:
        return False, "Registration not found"

    if registration.status != RegistrationStatus.REGISTERED:
        return False, f"Cannot re-sign: status is {registration.status.value}"

    # Check grace period (if set)
    book = registration.book
    if registration.re_sign_deadline and book.grace_period_days:
        grace_end = registration.re_sign_deadline + timedelta(
            days=book.grace_period_days
        )
        if datetime.utcnow() > grace_end:
            return False, "Re-sign period expired (past grace period)"

    return True, None


# --- Check Mark Operations ---


def record_check_mark(
    db: Session,
    registration_id: int,
    performed_by_id: int,
) -> BookRegistration:
    """
    Record a daily check mark for a member.

    Business Rules:
    - Only valid for REGISTERED status
    - Resets missed check mark counter
    - Creates RegistrationActivity record
    """
    registration = get_by_id(db, registration_id)
    if not registration:
        raise ValueError("Registration not found")

    if registration.status != RegistrationStatus.REGISTERED:
        raise ValueError("Cannot record check mark: not registered")

    if registration.is_exempt:
        raise ValueError("Exempt members do not need check marks")

    registration.has_check_mark = True
    registration.consecutive_missed_check_marks = 0
    registration.last_check_mark_at = datetime.utcnow()
    registration.last_check_mark_date = date.today()

    activity = RegistrationActivity(
        registration_id=registration_id,
        member_id=registration.member_id,
        book_id=registration.book_id,
        action=RegistrationAction.CHECK_MARK,
        previous_status=RegistrationStatus.REGISTERED,
        new_status=RegistrationStatus.REGISTERED,
        performed_by_id=performed_by_id,
        details="Check mark recorded",
    )
    db.add(activity)
    db.commit()
    db.refresh(registration)

    return registration


def record_missed_check_mark(
    db: Session,
    registration_id: int,
    performed_by_id: int,
    reason: Optional[NoCheckMarkReason] = None,
) -> BookRegistration:
    """
    Record a missed check mark.

    Business Rules:
    - Skip if member is exempt
    - Increment missed counter
    - If 3 consecutive misses -> auto roll-off
    - Creates RegistrationActivity record
    """
    registration = get_by_id(db, registration_id)
    if not registration:
        raise ValueError("Registration not found")

    if registration.status != RegistrationStatus.REGISTERED:
        raise ValueError("Cannot record missed check mark: not registered")

    # Skip exempt members
    if registration.is_exempt:
        return registration

    registration.consecutive_missed_check_marks += 1
    registration.check_marks += 1
    registration.has_check_mark = False
    registration.no_check_mark_reason = reason.value if reason else None

    # Check for auto roll-off (3rd check mark per Local 46 rules)
    if registration.check_marks >= 3:
        # Auto roll-off
        registration.status = RegistrationStatus.ROLLED_OFF
        registration.roll_off_date = datetime.utcnow()
        registration.roll_off_reason = RolloffReason.CHECK_MARKS

        activity = RegistrationActivity(
            registration_id=registration_id,
            member_id=registration.member_id,
            book_id=registration.book_id,
            action=RegistrationAction.ROLL_OFF,
            previous_status=RegistrationStatus.REGISTERED,
            new_status=RegistrationStatus.ROLLED_OFF,
            performed_by_id=performed_by_id,
            reason="3rd check mark - auto roll-off",
            details=f"Rolled off: 3 check marks",
        )
    else:
        activity = RegistrationActivity(
            registration_id=registration_id,
            member_id=registration.member_id,
            book_id=registration.book_id,
            action=RegistrationAction.CHECK_MARK_LOST,
            previous_status=RegistrationStatus.REGISTERED,
            new_status=RegistrationStatus.REGISTERED,
            performed_by_id=performed_by_id,
            details=f"Missed check mark ({registration.check_marks}/3)",
        )

    db.add(activity)
    db.commit()
    db.refresh(registration)

    return registration


def restore_check_mark(
    db: Session,
    registration_id: int,
    performed_by_id: int,
    reason: str,
) -> BookRegistration:
    """
    Restore a member's check mark (dispatcher override).

    Business Rules:
    - Resets has_check_mark to True
    - Decrements check mark count
    - Records the restoration reason
    - Creates RegistrationActivity record
    """
    registration = get_by_id(db, registration_id)
    if not registration:
        raise ValueError("Registration not found")

    if registration.status != RegistrationStatus.REGISTERED:
        raise ValueError("Cannot restore check mark: not registered")

    registration.has_check_mark = True
    registration.consecutive_missed_check_marks = 0
    registration.check_marks = max(0, registration.check_marks - 1)
    registration.check_mark_restored_at = datetime.utcnow()

    activity = RegistrationActivity(
        registration_id=registration_id,
        member_id=registration.member_id,
        book_id=registration.book_id,
        action=RegistrationAction.CHECK_MARK_RESTORED,
        previous_status=RegistrationStatus.REGISTERED,
        new_status=RegistrationStatus.REGISTERED,
        performed_by_id=performed_by_id,
        reason=reason,
        details=f"Check mark restored: {reason}",
    )
    db.add(activity)
    db.commit()
    db.refresh(registration)

    return registration


# --- Exempt Status Operations ---


def grant_exempt_status(
    db: Session,
    registration_id: int,
    performed_by_id: int,
    reason: ExemptReason,
    end_date: Optional[date] = None,
    notes: Optional[str] = None,
) -> BookRegistration:
    """
    Grant exempt status to a member on a book.

    Per Local 46 rules, exempt status can last up to 6 months
    unless extended by Business Manager.
    """
    registration = get_by_id(db, registration_id)
    if not registration:
        raise ValueError("Registration not found")

    registration.is_exempt = True
    registration.exempt_reason = reason
    registration.exempt_start_date = date.today()
    registration.exempt_end_date = end_date or (date.today() + timedelta(days=180))

    activity = RegistrationActivity(
        registration_id=registration_id,
        member_id=registration.member_id,
        book_id=registration.book_id,
        action=RegistrationAction.EXEMPT_START,
        previous_status=registration.status,
        new_status=registration.status,
        performed_by_id=performed_by_id,
        reason=reason.value,
        notes=notes,
        details=f"Exempt status granted: {reason.value}",
    )
    db.add(activity)
    db.commit()
    db.refresh(registration)

    return registration


def revoke_exempt_status(
    db: Session,
    registration_id: int,
    performed_by_id: int,
    reason: str,
) -> BookRegistration:
    """Revoke exempt status from a member."""
    registration = get_by_id(db, registration_id)
    if not registration:
        raise ValueError("Registration not found")

    registration.is_exempt = False
    registration.exempt_reason = None
    registration.exempt_end_date = None

    activity = RegistrationActivity(
        registration_id=registration_id,
        member_id=registration.member_id,
        book_id=registration.book_id,
        action=RegistrationAction.EXEMPT_END,
        previous_status=registration.status,
        new_status=registration.status,
        performed_by_id=performed_by_id,
        reason=reason,
        details="Exempt status revoked",
    )
    db.add(activity)
    db.commit()
    db.refresh(registration)

    return registration


# --- Roll-Off Operations ---


def process_roll_offs(db: Session, performed_by_id: int) -> list[BookRegistration]:
    """
    Batch process: find and roll off all expired registrations.

    Scans ALL active books for registrations where:
    - Status is REGISTERED
    - NOT exempt
    - NOT currently on a short call dispatch
    - re_sign_deadline + grace_period exceeded

    Returns list of registrations that were rolled off.
    """
    rolled_off = []
    now = datetime.utcnow()

    # Get all books with max_days or re_sign rules
    books = referral_book_service.get_all_active(db)

    for book in books:
        # Skip books without re-sign rules
        if not book.re_sign_days:
            continue

        grace_days = book.grace_period_days or 0

        # Find expired registrations
        expired = (
            db.query(BookRegistration)
            .filter(
                BookRegistration.book_id == book.id,
                BookRegistration.status == RegistrationStatus.REGISTERED,
                BookRegistration.is_exempt == False,
                BookRegistration.re_sign_deadline.isnot(None),
            )
            .all()
        )

        for reg in expired:
            # Check if past grace period
            if reg.re_sign_deadline:
                grace_end = reg.re_sign_deadline + timedelta(days=grace_days)
                if now > grace_end:
                    # Check protection
                    protected, _ = is_protected_from_rolloff(db, reg.id)
                    if not protected:
                        roll_off_member(
                            db,
                            reg.id,
                            performed_by_id,
                            RolloffReason.FAILED_RE_SIGN,
                            "Automatic rolloff - missed re-sign deadline",
                        )
                        rolled_off.append(reg)

    return rolled_off


def get_re_sign_reminders(db: Session) -> list[dict]:
    """
    Get members who need to re-sign soon.

    Returns list of dicts with:
    - registration info
    - days_remaining until roll-off
    - book info
    """
    reminders = []
    registrations = get_registrations_expiring_soon(db, days_threshold=7)

    for reg in registrations:
        if reg.re_sign_deadline:
            days_remaining = (reg.re_sign_deadline - datetime.utcnow()).days
            reminders.append(
                {
                    "registration_id": reg.id,
                    "member_id": reg.member_id,
                    "member_name": f"{reg.member.first_name} {reg.member.last_name}",
                    "member_number": reg.member.member_number,
                    "book_id": reg.book_id,
                    "book_name": reg.book.name,
                    "book_code": reg.book.code,
                    "re_sign_deadline": reg.re_sign_deadline,
                    "days_remaining": days_remaining,
                }
            )

    return reminders


def is_protected_from_rolloff(
    db: Session, registration_id: int
) -> Tuple[bool, Optional[str]]:
    """
    Check if a registration is protected from roll-off.

    Protected if:
    - Member is exempt
    - Member is currently on a short call dispatch
    - Member is currently dispatched (any type)

    Returns (True, reason) or (False, None).
    """
    registration = get_by_id(db, registration_id)
    if not registration:
        return False, None

    if registration.is_exempt:
        return True, "Member is exempt"

    if registration.status == RegistrationStatus.DISPATCHED:
        return True, "Member is currently dispatched"

    # Future: Check for active short call dispatch
    # This would require checking the Dispatch table

    return False, None


# --- Internal Helpers ---


def _get_queue_position(db: Session, book_id: int, apn: Decimal) -> int:
    """Get the queue position for a given APN."""
    count = (
        db.query(func.count(BookRegistration.id))
        .filter(
            BookRegistration.book_id == book_id,
            BookRegistration.status == RegistrationStatus.REGISTERED,
            BookRegistration.registration_number < apn,
        )
        .scalar()
    )
    return (count or 0) + 1
