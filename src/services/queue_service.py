"""
Service for centralized queue management and analytics.

Created: February 4, 2026 (Week 24 Session A/C)
Phase 7 - Referral & Dispatch System

Coordinates across BookRegistrationService and DispatchService
to provide a unified view of queue state. Queue ordering is ALWAYS
by APN (DECIMAL) — position numbers are derived.
"""
from typing import Optional, List
from datetime import datetime, date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case

from src.db.enums import (
    RegistrationStatus,
    DispatchStatus,
    BookClassification,
)
from src.models.book_registration import BookRegistration
from src.models.referral_book import ReferralBook
from src.models.dispatch import Dispatch
from src.models.member import Member
from src.services import referral_book_service
from src.services import book_registration_service


# --- Queue Snapshots ---


def get_queue_snapshot(
    db: Session,
    book_id: int,
    *,
    include_exempt: bool = False,
    limit: Optional[int] = None,
) -> list[dict]:
    """
    Full queue state with derived positions.

    Returns list of dicts ordered by APN:
    [
        {
            'position': 1,
            'member_id': 123,
            'member_name': 'John Smith',
            'member_number': 'A12345',
            'registration_id': 456,
            'registration_number': Decimal('45001.23'),
            'registered_date': datetime,
            'days_on_book': 45,
            'check_marks': 1,
            'has_check_mark': True,
            'is_exempt': False,
            'exempt_reason': None,
            'last_re_sign': datetime,
            're_sign_due': datetime,
        },
        ...
    ]
    """
    query = (
        db.query(BookRegistration)
        .filter(
            BookRegistration.book_id == book_id,
            BookRegistration.status == RegistrationStatus.REGISTERED,
        )
    )

    if not include_exempt:
        query = query.filter(BookRegistration.is_exempt == False)

    query = query.order_by(BookRegistration.registration_number.asc())

    if limit:
        query = query.limit(limit)

    registrations = query.all()

    snapshot = []
    for position, reg in enumerate(registrations, start=1):
        member = reg.member
        days_on_book = (datetime.utcnow() - reg.registration_date).days if reg.registration_date else 0

        snapshot.append({
            "position": position,
            "member_id": reg.member_id,
            "member_name": f"{member.first_name} {member.last_name}" if member else "Unknown",
            "member_number": member.member_number if member else None,
            "registration_id": reg.id,
            "registration_number": reg.registration_number,
            "registered_date": reg.registration_date,
            "days_on_book": days_on_book,
            "check_marks": reg.check_marks,
            "has_check_mark": reg.has_check_mark,
            "is_exempt": reg.is_exempt,
            "exempt_reason": reg.exempt_reason.value if reg.exempt_reason else None,
            "last_re_sign": reg.last_re_sign_date,
            "re_sign_due": reg.re_sign_deadline,
        })

    return snapshot


def get_multi_book_queue(
    db: Session,
    book_ids: list[int],
    *,
    include_exempt: bool = False,
) -> dict[int, list[dict]]:
    """
    Queue state across multiple books.

    Returns dict mapping book_id to queue snapshot.
    Useful for Wire members on Seattle + Bremerton + Pt Angeles.
    """
    result = {}
    for book_id in book_ids:
        result[book_id] = get_queue_snapshot(db, book_id, include_exempt=include_exempt)
    return result


# --- Next Eligible Selection ---


def get_next_eligible(
    db: Session,
    book_id: int,
    *,
    employer_id: Optional[int] = None,
    skip_member_ids: Optional[list[int]] = None,
) -> Optional[BookRegistration]:
    """
    Get next eligible member for dispatch.

    Skips:
    - Exempt members
    - Members with active blackout for this employer
    - Members with suspended bidding privileges (if web dispatch)
    - Rolled-off members

    Order: FIFO by APN (lowest first).
    """
    query = (
        db.query(BookRegistration)
        .filter(
            BookRegistration.book_id == book_id,
            BookRegistration.status == RegistrationStatus.REGISTERED,
            BookRegistration.is_exempt == False,
        )
        .order_by(BookRegistration.registration_number.asc())
    )

    registrations = query.all()

    for reg in registrations:
        # Skip if in skip list
        if skip_member_ids and reg.member_id in skip_member_ids:
            continue

        # Check blackout (if employer specified)
        if employer_id:
            from src.services import dispatch_service
            if dispatch_service.has_active_blackout(db, reg.member_id, employer_id):
                continue

        return reg

    return None


def get_queue_depth(db: Session, book_id: int) -> dict:
    """
    Queue depth analytics.

    Returns:
    {
        'total_registered': 150,
        'active': 130,
        'exempt': 12,
        'dispatched': 8,
        'eligible_for_dispatch': 120,
        'by_tier': {1: 80, 2: 40, 3: 10}  # if book has tier tracking
    }
    """
    book = referral_book_service.get_by_id(db, book_id)
    if not book:
        return {}

    # Count by status
    total = (
        db.query(func.count(BookRegistration.id))
        .filter(BookRegistration.book_id == book_id)
        .scalar()
        or 0
    )

    active = (
        db.query(func.count(BookRegistration.id))
        .filter(
            BookRegistration.book_id == book_id,
            BookRegistration.status == RegistrationStatus.REGISTERED,
        )
        .scalar()
        or 0
    )

    exempt = (
        db.query(func.count(BookRegistration.id))
        .filter(
            BookRegistration.book_id == book_id,
            BookRegistration.status == RegistrationStatus.REGISTERED,
            BookRegistration.is_exempt == True,
        )
        .scalar()
        or 0
    )

    dispatched = (
        db.query(func.count(BookRegistration.id))
        .filter(
            BookRegistration.book_id == book_id,
            BookRegistration.status == RegistrationStatus.DISPATCHED,
        )
        .scalar()
        or 0
    )

    eligible = active - exempt

    return {
        "book_id": book_id,
        "book_name": book.name,
        "book_code": book.code,
        "total_registered": total,
        "active": active,
        "exempt": exempt,
        "dispatched": dispatched,
        "eligible_for_dispatch": eligible,
    }


# --- Wait Time Estimation ---


def estimate_wait_time(db: Session, registration_id: int) -> dict:
    """
    Estimate days until dispatch based on historical rates.

    Returns:
    {
        'position': 15,
        'avg_dispatches_per_week': 3.2,
        'estimated_days': 33,
        'confidence': 'medium'  # low/medium/high based on data volume
    }
    """
    registration = book_registration_service.get_by_id(db, registration_id)
    if not registration:
        return {"error": "Registration not found"}

    if registration.status != RegistrationStatus.REGISTERED:
        return {"error": "Registration is not active"}

    book_id = registration.book_id
    position = book_registration_service.get_member_position(db, registration_id)

    # Calculate dispatch rate over last 30 days
    cutoff = datetime.utcnow() - timedelta(days=30)
    dispatch_count = (
        db.query(func.count(Dispatch.id))
        .join(BookRegistration)
        .filter(
            BookRegistration.book_id == book_id,
            Dispatch.dispatch_date >= cutoff,
        )
        .scalar()
        or 0
    )

    dispatches_per_week = dispatch_count / 4.3  # ~4.3 weeks in 30 days

    # Determine confidence
    if dispatch_count >= 20:
        confidence = "high"
    elif dispatch_count >= 5:
        confidence = "medium"
    else:
        confidence = "low"

    # Estimate days
    if dispatches_per_week > 0:
        estimated_weeks = position / dispatches_per_week
        estimated_days = int(estimated_weeks * 7)
    else:
        estimated_days = None  # Cannot estimate

    return {
        "registration_id": registration_id,
        "book_id": book_id,
        "position": position,
        "avg_dispatches_per_week": round(dispatches_per_week, 2),
        "estimated_days": estimated_days,
        "confidence": confidence,
    }


# --- Position History ---


def get_position_history(
    db: Session,
    registration_id: int,
    days: int = 30,
) -> list[dict]:
    """
    How a member's position changed over time.

    For member profile and fairness auditing.
    """
    from src.models.registration_activity import RegistrationActivity
    from src.db.enums import RegistrationAction

    cutoff = datetime.utcnow() - timedelta(days=days)

    activities = (
        db.query(RegistrationActivity)
        .filter(
            RegistrationActivity.registration_id == registration_id,
            RegistrationActivity.created_at >= cutoff,
            RegistrationActivity.new_position.isnot(None),
        )
        .order_by(RegistrationActivity.created_at.asc())
        .all()
    )

    history = []
    for activity in activities:
        history.append({
            "date": activity.created_at,
            "action": activity.action.value if activity.action else None,
            "previous_position": activity.previous_position,
            "new_position": activity.new_position,
        })

    return history


# --- Analytics ---


def get_book_utilization(
    db: Session,
    book_id: int,
    period_days: int = 30,
) -> dict:
    """
    Dispatch rate, avg days on book, turnover for a book.
    """
    book = referral_book_service.get_by_id(db, book_id)
    if not book:
        return {}

    cutoff = datetime.utcnow() - timedelta(days=period_days)

    # Count dispatches
    total_dispatches = (
        db.query(func.count(Dispatch.id))
        .join(BookRegistration)
        .filter(
            BookRegistration.book_id == book_id,
            Dispatch.dispatch_date >= cutoff,
        )
        .scalar()
        or 0
    )

    # Current registered count
    current_registered = (
        db.query(func.count(BookRegistration.id))
        .filter(
            BookRegistration.book_id == book_id,
            BookRegistration.status == RegistrationStatus.REGISTERED,
        )
        .scalar()
        or 0
    )

    # Average days on book for active registrations
    avg_days = (
        db.query(func.avg(func.extract('day', datetime.utcnow() - BookRegistration.registration_date)))
        .filter(
            BookRegistration.book_id == book_id,
            BookRegistration.status == RegistrationStatus.REGISTERED,
        )
        .scalar()
        or 0
    )

    dispatches_per_week = total_dispatches / (period_days / 7) if period_days > 0 else 0
    turnover_rate = total_dispatches / current_registered if current_registered > 0 else 0

    return {
        "book_id": book_id,
        "book_name": book.name,
        "period_days": period_days,
        "total_dispatches": total_dispatches,
        "dispatches_per_week": round(dispatches_per_week, 2),
        "avg_days_on_book": int(avg_days) if avg_days else 0,
        "current_registered": current_registered,
        "turnover_rate": round(turnover_rate, 3),
    }


def get_dispatch_rate(
    db: Session,
    book_id: int,
    period: str = "week",  # week, month
) -> dict:
    """
    Dispatches per day/week/month per book.
    """
    if period == "week":
        days = 7
    elif period == "month":
        days = 30
    else:
        days = 7

    cutoff = datetime.utcnow() - timedelta(days=days)

    count = (
        db.query(func.count(Dispatch.id))
        .join(BookRegistration)
        .filter(
            BookRegistration.book_id == book_id,
            Dispatch.dispatch_date >= cutoff,
        )
        .scalar()
        or 0
    )

    rate_per_day = count / days if days > 0 else 0

    return {
        "book_id": book_id,
        "period": period,
        "period_days": days,
        "total_dispatches": count,
        "rate_per_day": round(rate_per_day, 2),
    }


def get_classification_summary(db: Session) -> list[dict]:
    """
    Cross-book summary by classification.

    For landing page display.
    """
    summaries = []

    # Group books by classification
    books = referral_book_service.get_all_active(db)
    classifications = {}

    for book in books:
        cls = book.classification.value if book.classification else "unknown"
        if cls not in classifications:
            classifications[cls] = []
        classifications[cls].append(book)

    for classification, book_list in classifications.items():
        book_ids = [b.id for b in book_list]
        book_names = [b.name for b in book_list]

        # Aggregate stats
        total_registered = 0
        total_active = 0
        total_dispatched_30d = 0

        for book in book_list:
            stats = get_book_utilization(db, book.id, period_days=30)
            depth = get_queue_depth(db, book.id)
            total_registered += depth.get("total_registered", 0)
            total_active += depth.get("active", 0)
            total_dispatched_30d += stats.get("total_dispatches", 0)

        # Calculate average wait
        avg_wait_days = 0
        if total_dispatched_30d > 0 and total_active > 0:
            # Rough estimate: (active / dispatches_per_month) * 30
            avg_wait_days = int((total_active / total_dispatched_30d) * 30)

        summaries.append({
            "classification": classification,
            "books": book_names,
            "book_ids": book_ids,
            "total_registered": total_registered,
            "total_active": total_active,
            "total_dispatched_30d": total_dispatched_30d,
            "avg_wait_days": avg_wait_days,
        })

    return summaries


def get_member_queue_status(db: Session, member_id: int) -> dict:
    """
    All books a member is on, with positions.

    For member profile display.
    """
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return {"error": "Member not found"}

    registrations = book_registration_service.get_member_registrations(db, member_id, active_only=True)

    reg_list = []
    for reg in registrations:
        book = reg.book
        position = book_registration_service.get_member_position(db, reg.id)

        # Get total on book
        depth = get_queue_depth(db, reg.book_id)

        days_on_book = (datetime.utcnow() - reg.registration_date).days if reg.registration_date else 0

        reg_list.append({
            "book_id": reg.book_id,
            "book_name": book.name if book else "Unknown",
            "book_code": book.code if book else None,
            "book_number": book.book_number if book else None,
            "position": position,
            "total_on_book": depth.get("active", 0),
            "registration_id": reg.id,
            "registration_number": str(reg.registration_number),
            "registered_date": reg.registration_date,
            "days_on_book": days_on_book,
            "check_marks": reg.check_marks,
            "has_check_mark": reg.has_check_mark,
            "is_exempt": reg.is_exempt,
            "exempt_reason": reg.exempt_reason.value if reg.exempt_reason else None,
            "re_sign_due": reg.re_sign_deadline,
            "status": reg.status.value,
        })

    return {
        "member_id": member_id,
        "member_name": f"{member.first_name} {member.last_name}",
        "member_number": member.member_number,
        "registrations": reg_list,
        "total_books": len(reg_list),
    }


def get_daily_activity_log(
    db: Session,
    target_date: Optional[date] = None,
) -> list[dict]:
    """
    All queue changes for a given day.

    For daily operations report.
    """
    from src.models.registration_activity import RegistrationActivity

    if target_date is None:
        target_date = date.today()

    start = datetime.combine(target_date, datetime.min.time())
    end = datetime.combine(target_date, datetime.max.time())

    activities = (
        db.query(RegistrationActivity)
        .filter(
            RegistrationActivity.created_at >= start,
            RegistrationActivity.created_at <= end,
        )
        .order_by(RegistrationActivity.created_at.asc())
        .all()
    )

    log = []
    for activity in activities:
        log.append({
            "timestamp": activity.created_at,
            "registration_id": activity.registration_id,
            "member_id": activity.member_id,
            "book_id": activity.book_id,
            "action": activity.action.value if activity.action else None,
            "previous_status": activity.previous_status.value if activity.previous_status else None,
            "new_status": activity.new_status.value if activity.new_status else None,
            "details": activity.details,
        })

    return log
