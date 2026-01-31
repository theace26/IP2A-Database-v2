"""Service for dues payment operations."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.db.enums import DuesPaymentStatus, MemberStatus
from src.models.dues_payment import DuesPayment
from src.models.dues_period import DuesPeriod
from src.models.member import Member
from src.schemas.dues_payment import (
    DuesPaymentCreate,
    DuesPaymentRecord,
    DuesPaymentUpdate,
    MemberDuesSummary,
)
from src.services import dues_rate_service, dues_period_service


def get_payment(db: Session, payment_id: int) -> Optional[DuesPayment]:
    """Get a payment by ID."""
    return db.query(DuesPayment).filter(
        DuesPayment.id == payment_id,
        DuesPayment.deleted_at.is_(None)
    ).first()


def get_member_payments(
    db: Session,
    member_id: int,
    year: Optional[int] = None,
    status: Optional[DuesPaymentStatus] = None
) -> list[DuesPayment]:
    """Get all payments for a member."""
    query = db.query(DuesPayment).join(DuesPayment.period).filter(
        DuesPayment.member_id == member_id,
        DuesPayment.deleted_at.is_(None)
    )

    if year:
        query = query.filter(DuesPeriod.period_year == year)

    if status:
        query = query.filter(DuesPayment.status == status)

    return query.order_by(DuesPeriod.period_year.desc(), DuesPeriod.period_month.desc()).all()


def get_period_payments(
    db: Session,
    period_id: int,
    status: Optional[DuesPaymentStatus] = None
) -> list[DuesPayment]:
    """Get all payments for a period."""
    query = db.query(DuesPayment).filter(
        DuesPayment.period_id == period_id,
        DuesPayment.deleted_at.is_(None)
    )

    if status:
        query = query.filter(DuesPayment.status == status)

    return query.all()


def get_overdue_payments(db: Session) -> list[DuesPayment]:
    """Get all overdue payments."""
    return db.query(DuesPayment).filter(
        DuesPayment.status == DuesPaymentStatus.OVERDUE,
        DuesPayment.deleted_at.is_(None)
    ).all()


def get_all_payments(
    db: Session,
    status: Optional[DuesPaymentStatus] = None,
    skip: int = 0,
    limit: int = 100
) -> list[DuesPayment]:
    """Get all payments with optional filtering."""
    query = db.query(DuesPayment).filter(DuesPayment.deleted_at.is_(None))
    if status:
        query = query.filter(DuesPayment.status == status)
    return query.order_by(DuesPayment.id.desc()).offset(skip).limit(limit).all()


def create_payment_record(
    db: Session,
    data: DuesPaymentCreate
) -> DuesPayment:
    """Create a new payment record (typically when generating for a period)."""
    # Generate receipt number
    receipt_number = f"RCP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    payment = DuesPayment(
        **data.model_dump(),
        receipt_number=receipt_number,
        status=DuesPaymentStatus.PENDING
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def record_payment(
    db: Session,
    payment_id: int,
    data: DuesPaymentRecord,
    processed_by_id: int
) -> Optional[DuesPayment]:
    """Record a payment against a dues record."""
    payment = get_payment(db, payment_id)
    if not payment:
        return None

    payment.amount_paid = Decimal(str(payment.amount_paid)) + data.amount_paid
    payment.payment_date = data.payment_date
    payment.payment_method = data.payment_method
    payment.reference_number = data.reference_number
    payment.notes = data.notes
    payment.processed_by_id = processed_by_id
    payment.processed_at = datetime.utcnow()

    # Update status
    if Decimal(str(payment.amount_paid)) >= Decimal(str(payment.amount_due)):
        payment.status = DuesPaymentStatus.PAID
    elif Decimal(str(payment.amount_paid)) > 0:
        payment.status = DuesPaymentStatus.PARTIAL

    db.commit()
    db.refresh(payment)
    return payment


def update_payment(
    db: Session,
    payment_id: int,
    data: DuesPaymentUpdate
) -> Optional[DuesPayment]:
    """Update a payment."""
    payment = get_payment(db, payment_id)
    if not payment:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(payment, field, value)

    db.commit()
    db.refresh(payment)
    return payment


def generate_period_dues(
    db: Session,
    period_id: int,
    member_ids: Optional[list[int]] = None
) -> list[DuesPayment]:
    """Generate dues records for all active members for a period."""
    period = dues_period_service.get_period(db, period_id)
    if not period:
        raise ValueError(f"Period {period_id} not found")

    # Get active members
    query = db.query(Member).filter(Member.status == MemberStatus.ACTIVE)
    if member_ids:
        query = query.filter(Member.id.in_(member_ids))

    members = query.all()
    payments = []

    for member in members:
        # Check if payment record already exists
        existing = db.query(DuesPayment).filter(
            DuesPayment.member_id == member.id,
            DuesPayment.period_id == period_id,
            DuesPayment.deleted_at.is_(None)
        ).first()

        if existing:
            payments.append(existing)
            continue

        # Get rate for this member's classification
        rate = dues_rate_service.get_rate_for_date(
            db,
            member.classification,
            date(period.period_year, period.period_month, 1)
        )

        if not rate:
            continue  # Skip if no rate defined

        payment = DuesPayment(
            member_id=member.id,
            period_id=period_id,
            amount_due=rate.monthly_amount,
            status=DuesPaymentStatus.PENDING,
            receipt_number=f"RCP-{period.period_year}{period.period_month:02d}-{uuid.uuid4().hex[:8].upper()}"
        )
        db.add(payment)
        payments.append(payment)

    db.commit()
    return payments


def update_overdue_status(db: Session) -> int:
    """Update status to OVERDUE for past-grace-period unpaid dues. Returns count updated."""
    today = date.today()

    # Find payments that should be marked overdue
    payments = db.query(DuesPayment).join(DuesPayment.period).filter(
        and_(
            DuesPayment.status.in_([DuesPaymentStatus.PENDING, DuesPaymentStatus.DUE, DuesPaymentStatus.PARTIAL]),
            DuesPeriod.grace_period_end < today,
            DuesPayment.deleted_at.is_(None)
        )
    ).all()

    count = 0
    for payment in payments:
        if Decimal(str(payment.amount_paid)) < Decimal(str(payment.amount_due)):
            payment.status = DuesPaymentStatus.OVERDUE
            count += 1

    db.commit()
    return count


def get_member_dues_summary(db: Session, member_id: int) -> Optional[MemberDuesSummary]:
    """Get summary of member's dues status."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return None

    payments = get_member_payments(db, member_id)

    total_due = sum(Decimal(str(p.amount_due)) for p in payments)
    total_paid = sum(Decimal(str(p.amount_paid)) for p in payments)
    overdue_count = len([p for p in payments if p.status == DuesPaymentStatus.OVERDUE])

    last_payment = max(
        (p.payment_date for p in payments if p.payment_date),
        default=None
    )

    return MemberDuesSummary(
        member_id=member.id,
        member_name=f"{member.first_name} {member.last_name}",
        classification=member.classification.value,
        total_due=total_due,
        total_paid=total_paid,
        balance=total_due - total_paid,
        periods_overdue=overdue_count,
        last_payment_date=last_payment
    )


def delete_payment(db: Session, payment_id: int) -> bool:
    """Soft delete a payment."""
    payment = get_payment(db, payment_id)
    if not payment:
        return False
    payment.deleted_at = datetime.utcnow()
    payment.is_deleted = True
    db.commit()
    return True
