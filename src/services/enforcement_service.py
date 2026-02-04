"""
Service for automated enforcement of dispatch business rules.

Created: February 4, 2026 (Week 24 Session B)
Phase 7 - Referral & Dispatch System

Batch processing for re-sign deadlines, expired registration cleanup,
and check mark enforcement. Designed for scheduled tasks or admin triggers.
"""
from typing import Optional, List
from datetime import datetime, date, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from src.db.enums import (
    RegistrationStatus,
    RolloffReason,
    LaborRequestStatus,
    BidStatus,
)
from src.models.book_registration import BookRegistration
from src.models.referral_book import ReferralBook
from src.models.labor_request import LaborRequest
from src.models.job_bid import JobBid
from src.services import referral_book_service
from src.services import book_registration_service
from src.services import labor_request_service
from src.services import job_bid_service


# --- Constants (per Local 46 Rules) ---
RE_SIGN_DEADLINE_DAYS = 30
RE_SIGN_REMINDER_DAYS = 7   # Remind 7 days before deadline
BLACKOUT_DURATION_DAYS = 14
SUSPENSION_DURATION_MONTHS = 12
EXEMPT_GRACE_PERIOD_DAYS = 7  # Grace period after exempt ends


# --- Master Enforcement Run ---


def daily_enforcement_run(
    db: Session,
    *,
    dry_run: bool = False,
    performed_by_id: Optional[int] = None,
) -> dict:
    """
    Master enforcement method — runs all checks.

    If dry_run=True, returns report of what WOULD happen without making changes.

    Returns:
    {
        'timestamp': datetime,
        'dry_run': bool,
        're_sign_rolloffs': 5,
        're_sign_reminders': 12,
        'expired_requests': 3,
        'expired_exemptions': 1,
        'expired_blackouts': 2,
        'expired_suspensions': 0,
        'expired_bids': 8,
        'details': [...]
    }
    """
    timestamp = datetime.utcnow()
    details = []

    # System user ID for automated actions
    system_user_id = performed_by_id or 1

    # 1. Re-sign deadline enforcement
    re_sign_results = enforce_re_sign_deadlines(db, dry_run=dry_run, performed_by_id=system_user_id)
    details.extend(re_sign_results)
    re_sign_rolloffs = len([r for r in re_sign_results if r.get("action") == "rolled_off"])

    # 2. Re-sign reminders
    reminders = send_re_sign_reminders(db)
    re_sign_reminders = len(reminders)

    # 3. Expired requests
    request_results = process_expired_requests(db, dry_run=dry_run)
    details.extend(request_results)
    expired_requests = len(request_results)

    # 4. Expired exemptions
    exemption_results = process_expired_exemptions(db, dry_run=dry_run, performed_by_id=system_user_id)
    details.extend(exemption_results)
    expired_exemptions = len(exemption_results)

    # 5. Expired bids
    bid_results = process_expired_bids(db, dry_run=dry_run)
    details.extend(bid_results)
    expired_bids = len(bid_results)

    # Note: Blackout and suspension cleanup is implicit via date checks
    # No separate table to clean up in current implementation

    return {
        "timestamp": timestamp,
        "dry_run": dry_run,
        "re_sign_rolloffs": re_sign_rolloffs,
        "re_sign_reminders": re_sign_reminders,
        "expired_requests": expired_requests,
        "expired_exemptions": expired_exemptions,
        "expired_blackouts": 0,  # Handled via date checks
        "expired_suspensions": 0,  # Handled via date checks
        "expired_bids": expired_bids,
        "total_actions": re_sign_rolloffs + expired_requests + expired_exemptions + expired_bids,
        "details": details,
    }


def get_enforcement_report(db: Session) -> dict:
    """
    Preview what enforcement would do without making changes.

    Calls daily_enforcement_run with dry_run=True.
    For admin dashboard display.
    """
    return daily_enforcement_run(db, dry_run=True)


# --- Re-Sign Deadline Enforcement (Rule 7) ---


def enforce_re_sign_deadlines(
    db: Session,
    *,
    dry_run: bool = False,
    performed_by_id: int,
) -> list[dict]:
    """
    Process all registrations past 30-day re-sign deadline.

    Skips exempt members (Rule 14).
    Returns list of affected registrations with action taken.
    """
    now = datetime.utcnow()
    results = []

    # Find all non-exempt registrations past deadline
    overdue = (
        db.query(BookRegistration)
        .filter(
            BookRegistration.status == RegistrationStatus.REGISTERED,
            BookRegistration.is_exempt == False,
            BookRegistration.re_sign_deadline.isnot(None),
            BookRegistration.re_sign_deadline < now,
        )
        .all()
    )

    for registration in overdue:
        book = registration.book
        grace_days = book.grace_period_days if book else 0
        grace_end = registration.re_sign_deadline + timedelta(days=grace_days)

        if now > grace_end:
            # Check if protected
            protected, reason = book_registration_service.is_protected_from_rolloff(db, registration.id)

            if protected:
                results.append({
                    "registration_id": registration.id,
                    "member_id": registration.member_id,
                    "book_id": registration.book_id,
                    "action": "skipped",
                    "reason": f"Protected: {reason}",
                    "deadline": registration.re_sign_deadline,
                })
                continue

            result = {
                "registration_id": registration.id,
                "member_id": registration.member_id,
                "book_id": registration.book_id,
                "book_name": book.name if book else "Unknown",
                "deadline": registration.re_sign_deadline,
                "grace_end": grace_end,
                "days_overdue": (now - grace_end).days,
            }

            if dry_run:
                result["action"] = "would_roll_off"
            else:
                book_registration_service.roll_off_member(
                    db,
                    registration.id,
                    performed_by_id,
                    RolloffReason.FAILED_RE_SIGN,
                    "Automatic rolloff - missed re-sign deadline",
                )
                result["action"] = "rolled_off"

            results.append(result)

    return results


def send_re_sign_reminders(db: Session) -> list[dict]:
    """
    Flag members with re-sign due within 7 days.

    Returns list of registrations needing reminders.
    Does NOT roll off — just flags for notification.
    """
    reminders = []
    registrations = book_registration_service.get_registrations_expiring_soon(
        db, days_threshold=RE_SIGN_REMINDER_DAYS
    )

    for reg in registrations:
        if reg.re_sign_deadline:
            days_remaining = (reg.re_sign_deadline - datetime.utcnow()).days
            reminders.append({
                "registration_id": reg.id,
                "member_id": reg.member_id,
                "book_id": reg.book_id,
                "member_name": f"{reg.member.first_name} {reg.member.last_name}" if reg.member else "Unknown",
                "book_name": reg.book.name if reg.book else "Unknown",
                "re_sign_deadline": reg.re_sign_deadline,
                "days_remaining": days_remaining,
                "action": "reminder_flagged",
            })

    return reminders


# --- Expired Request Processing ---


def process_expired_requests(
    db: Session,
    *,
    dry_run: bool = False,
) -> list[dict]:
    """
    Expire unfilled labor requests past their target date.
    """
    today = date.today()
    results = []

    old_requests = (
        db.query(LaborRequest)
        .filter(
            LaborRequest.status.in_([LaborRequestStatus.OPEN, LaborRequestStatus.PARTIALLY_FILLED]),
            LaborRequest.start_date < today,
        )
        .all()
    )

    for request in old_requests:
        result = {
            "request_id": request.id,
            "request_number": request.request_number,
            "employer_id": request.employer_id,
            "employer_name": request.employer_name,
            "start_date": request.start_date,
            "workers_requested": request.workers_requested,
            "workers_dispatched": request.workers_dispatched,
        }

        if dry_run:
            result["action"] = "would_expire"
        else:
            request.status = LaborRequestStatus.EXPIRED
            result["action"] = "expired"

        results.append(result)

    if not dry_run and results:
        db.commit()

    return results


# --- Expired Exemption Processing ---


def process_expired_exemptions(
    db: Session,
    *,
    dry_run: bool = False,
    performed_by_id: int,
) -> list[dict]:
    """
    Revoke exempt status where end_date has passed.

    After revocation, member's re-sign timer resumes.
    If re-sign would now be overdue, give grace period (end_date + 7 days).
    """
    today = date.today()
    results = []

    # Find expired exemptions
    expired_exemptions = (
        db.query(BookRegistration)
        .filter(
            BookRegistration.status == RegistrationStatus.REGISTERED,
            BookRegistration.is_exempt == True,
            BookRegistration.exempt_end_date.isnot(None),
            BookRegistration.exempt_end_date < today,
        )
        .all()
    )

    for registration in expired_exemptions:
        result = {
            "registration_id": registration.id,
            "member_id": registration.member_id,
            "book_id": registration.book_id,
            "exempt_reason": registration.exempt_reason.value if registration.exempt_reason else None,
            "exempt_end_date": registration.exempt_end_date,
        }

        if dry_run:
            result["action"] = "would_revoke_exempt"
        else:
            # Revoke exempt status
            registration.is_exempt = False
            registration.exempt_reason = None

            # Reset re-sign deadline with grace period
            new_deadline = datetime.utcnow() + timedelta(days=EXEMPT_GRACE_PERIOD_DAYS)
            registration.re_sign_deadline = new_deadline
            registration.last_re_sign_date = datetime.utcnow()

            result["action"] = "exempt_revoked"
            result["new_re_sign_deadline"] = new_deadline

        results.append(result)

    if not dry_run and results:
        db.commit()

    return results


# --- Expired Bid Processing ---


def process_expired_bids(
    db: Session,
    *,
    dry_run: bool = False,
) -> list[dict]:
    """
    Expire bids on requests that are no longer open.
    """
    results = []

    # Find pending bids on closed requests
    expired_bids = (
        db.query(JobBid)
        .join(LaborRequest)
        .filter(
            JobBid.bid_status == BidStatus.PENDING,
            LaborRequest.status.not_in([LaborRequestStatus.OPEN, LaborRequestStatus.PARTIALLY_FILLED]),
        )
        .all()
    )

    for bid in expired_bids:
        result = {
            "bid_id": bid.id,
            "labor_request_id": bid.labor_request_id,
            "member_id": bid.member_id,
            "bid_submitted_at": bid.bid_submitted_at,
        }

        if dry_run:
            result["action"] = "would_expire"
        else:
            bid.bid_status = BidStatus.EXPIRED
            result["action"] = "expired"

        results.append(result)

    if not dry_run and results:
        db.commit()

    return results


# --- Check Mark Enforcement ---


def enforce_check_mark_limits(db: Session, *, dry_run: bool = False) -> list[dict]:
    """
    Batch verify check mark counts.

    Rule 10: 3rd check mark = roll off. This is normally handled in real-time
    by record_missed_check_mark, but this method catches any edge cases.
    """
    results = []

    # Find registrations with 3+ check marks still active
    over_limit = (
        db.query(BookRegistration)
        .filter(
            BookRegistration.status == RegistrationStatus.REGISTERED,
            BookRegistration.check_marks >= 3,
            BookRegistration.is_exempt == False,
        )
        .all()
    )

    for registration in over_limit:
        result = {
            "registration_id": registration.id,
            "member_id": registration.member_id,
            "book_id": registration.book_id,
            "check_marks": registration.check_marks,
        }

        if dry_run:
            result["action"] = "would_roll_off"
        else:
            # Note: Normally this would call book_registration_service.roll_off_member
            # but we'd need performed_by_id. For now, flag it.
            result["action"] = "needs_rolloff"
            result["reason"] = "3+ check marks but still registered"

        results.append(result)

    return results


# --- Utility Methods ---


def get_pending_enforcements(db: Session) -> dict:
    """
    Get counts of items pending enforcement.

    For dashboard "pending actions" display.
    """
    now = datetime.utcnow()
    today = date.today()

    # Overdue re-signs
    overdue_re_signs = (
        db.query(func.count(BookRegistration.id))
        .filter(
            BookRegistration.status == RegistrationStatus.REGISTERED,
            BookRegistration.is_exempt == False,
            BookRegistration.re_sign_deadline.isnot(None),
            BookRegistration.re_sign_deadline < now,
        )
        .scalar()
        or 0
    )

    # Upcoming re-signs (next 7 days)
    upcoming_deadline = now + timedelta(days=7)
    upcoming_re_signs = (
        db.query(func.count(BookRegistration.id))
        .filter(
            BookRegistration.status == RegistrationStatus.REGISTERED,
            BookRegistration.is_exempt == False,
            BookRegistration.re_sign_deadline.isnot(None),
            BookRegistration.re_sign_deadline >= now,
            BookRegistration.re_sign_deadline <= upcoming_deadline,
        )
        .scalar()
        or 0
    )

    # Expired requests
    expired_requests = (
        db.query(func.count(LaborRequest.id))
        .filter(
            LaborRequest.status.in_([LaborRequestStatus.OPEN, LaborRequestStatus.PARTIALLY_FILLED]),
            LaborRequest.start_date < today,
        )
        .scalar()
        or 0
    )

    # Expired exemptions
    expired_exemptions = (
        db.query(func.count(BookRegistration.id))
        .filter(
            BookRegistration.is_exempt == True,
            BookRegistration.exempt_end_date.isnot(None),
            BookRegistration.exempt_end_date < today,
        )
        .scalar()
        or 0
    )

    # Over check mark limit
    over_check_limit = (
        db.query(func.count(BookRegistration.id))
        .filter(
            BookRegistration.status == RegistrationStatus.REGISTERED,
            BookRegistration.check_marks >= 3,
            BookRegistration.is_exempt == False,
        )
        .scalar()
        or 0
    )

    return {
        "overdue_re_signs": overdue_re_signs,
        "upcoming_re_signs": upcoming_re_signs,
        "expired_requests": expired_requests,
        "expired_exemptions": expired_exemptions,
        "over_check_limit": over_check_limit,
        "total_pending": overdue_re_signs + expired_requests + expired_exemptions + over_check_limit,
    }


def run_specific_enforcement(
    db: Session,
    enforcement_type: str,
    *,
    dry_run: bool = False,
    performed_by_id: int,
) -> list[dict]:
    """
    Run a specific enforcement type.

    Types: 're_sign', 'requests', 'exemptions', 'bids', 'check_marks'
    """
    if enforcement_type == "re_sign":
        return enforce_re_sign_deadlines(db, dry_run=dry_run, performed_by_id=performed_by_id)
    elif enforcement_type == "requests":
        return process_expired_requests(db, dry_run=dry_run)
    elif enforcement_type == "exemptions":
        return process_expired_exemptions(db, dry_run=dry_run, performed_by_id=performed_by_id)
    elif enforcement_type == "bids":
        return process_expired_bids(db, dry_run=dry_run)
    elif enforcement_type == "check_marks":
        return enforce_check_mark_limits(db, dry_run=dry_run)
    else:
        raise ValueError(f"Unknown enforcement type: {enforcement_type}")
