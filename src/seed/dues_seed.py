"""Seed dues tracking data."""

from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from faker import Faker

from src.db.enums import (
    MemberClassification,
    MemberStatus,
    DuesPaymentMethod,
    DuesPaymentStatus,
    DuesAdjustmentType,
    AdjustmentStatus,
)
from src.models.dues_rate import DuesRate
from src.models.dues_period import DuesPeriod
from src.models.dues_payment import DuesPayment
from src.models.dues_adjustment import DuesAdjustment
from src.models.member import Member
from src.models.user import User
from .base_seed import add_records

fake = Faker()


def seed_dues_rates(db: Session) -> list[DuesRate]:
    """Seed dues rate schedule by classification."""
    rates = []

    # Define monthly dues by classification
    # apprentice_1 through apprentice_5 have graduated rates
    rate_schedule = {
        MemberClassification.APPRENTICE_1ST_YEAR: Decimal("35.00"),
        MemberClassification.APPRENTICE_2ND_YEAR: Decimal("40.00"),
        MemberClassification.APPRENTICE_3RD_YEAR: Decimal("45.00"),
        MemberClassification.APPRENTICE_4TH_YEAR: Decimal("50.00"),
        MemberClassification.APPRENTICE_5TH_YEAR: Decimal("55.00"),
        MemberClassification.JOURNEYMAN: Decimal("75.00"),
        MemberClassification.FOREMAN: Decimal("85.00"),
        MemberClassification.RETIREE: Decimal("25.00"),
        MemberClassification.HONORARY: Decimal("0.00"),
    }

    # Create rates effective from start of current year
    effective_date = date(date.today().year, 1, 1)

    for classification, amount in rate_schedule.items():
        rate = DuesRate(
            classification=classification,
            monthly_amount=amount,
            effective_date=effective_date,
            end_date=None,  # Current rate
            description=f"{classification.value.replace('_', ' ').title()} monthly dues rate"
        )
        rates.append(rate)

    add_records(db, rates)
    print(f"  - Created {len(rates)} dues rates")
    return rates


def seed_dues_periods(db: Session) -> list[DuesPeriod]:
    """Seed dues periods for current and previous year."""
    periods = []

    current_year = date.today().year
    current_month = date.today().month

    # Create periods for last 12 months
    for i in range(12):
        year = current_year
        month = current_month - i

        while month <= 0:
            month += 12
            year -= 1

        # Due date is 1st of the month
        due_date = date(year, month, 1)

        # Grace period is 15 days
        grace_period_end = due_date + timedelta(days=15)

        # Past periods (before current month) are closed
        is_past = (year < current_year) or (year == current_year and month < current_month)

        period = DuesPeriod(
            period_year=year,
            period_month=month,
            due_date=due_date,
            grace_period_end=grace_period_end,
            is_closed=is_past,
            closed_at=grace_period_end + timedelta(days=5) if is_past else None,
            notes=None
        )
        periods.append(period)

    add_records(db, periods)
    print(f"  - Created {len(periods)} dues periods")
    return periods


def seed_dues_payments(db: Session, periods: list[DuesPeriod]) -> list[DuesPayment]:
    """Seed dues payment records for active members."""
    payments = []

    # Get active members
    members = db.query(Member).filter(Member.status == MemberStatus.ACTIVE).all()

    if not members:
        print("  - No active members found, skipping payments")
        return payments

    # Get rates by classification
    rates = db.query(DuesRate).filter(DuesRate.end_date.is_(None)).all()
    rate_map = {r.classification: r.monthly_amount for r in rates}

    payment_methods = [
        DuesPaymentMethod.PAYROLL_DEDUCTION,
        DuesPaymentMethod.CHECK,
        DuesPaymentMethod.CASH,
        DuesPaymentMethod.CREDIT_CARD,
        DuesPaymentMethod.ACH_TRANSFER,
    ]

    for period in periods:
        for member in members:
            amount_due = rate_map.get(member.classification, Decimal("50.00"))

            # Determine payment status based on period age
            is_past_period = period.is_closed

            if is_past_period:
                # 90% paid, 5% partial, 5% overdue
                rand = fake.random_int(min=1, max=100)
                if rand <= 90:
                    status = DuesPaymentStatus.PAID
                    amount_paid = amount_due
                    payment_date = period.due_date + timedelta(days=fake.random_int(min=0, max=14))
                    payment_method = fake.random_element(payment_methods)
                elif rand <= 95:
                    status = DuesPaymentStatus.PARTIAL
                    amount_paid = amount_due / 2
                    payment_date = period.due_date + timedelta(days=fake.random_int(min=0, max=14))
                    payment_method = fake.random_element(payment_methods)
                else:
                    status = DuesPaymentStatus.OVERDUE
                    amount_paid = Decimal("0.00")
                    payment_date = None
                    payment_method = None
            else:
                # Current/future period - pending
                status = DuesPaymentStatus.PENDING
                amount_paid = Decimal("0.00")
                payment_date = None
                payment_method = None

            receipt_number = f"RCP-{period.period_year}{period.period_month:02d}-{fake.uuid4()[:8].upper()}"

            payment = DuesPayment(
                member_id=member.id,
                period_id=period.id,
                amount_due=amount_due,
                amount_paid=amount_paid,
                status=status,
                payment_date=payment_date,
                payment_method=payment_method,
                receipt_number=receipt_number,
                reference_number=f"REF-{fake.random_int(min=10000, max=99999)}" if payment_date else None,
                notes=None
            )
            payments.append(payment)

    add_records(db, payments)
    print(f"  - Created {len(payments)} dues payments")
    return payments


def seed_dues_adjustments(db: Session, payments: list[DuesPayment]) -> list[DuesAdjustment]:
    """Seed some adjustment requests."""
    adjustments = []

    # Get a user for the requestor (if any exist)
    user = db.query(User).first()
    requestor_id = user.id if user else 1

    adjustment_types = [
        DuesAdjustmentType.WAIVER,
        DuesAdjustmentType.HARDSHIP,
        DuesAdjustmentType.CREDIT,
        DuesAdjustmentType.CORRECTION,
        DuesAdjustmentType.LATE_FEE,
    ]

    # Create 10-20 random adjustments
    num_adjustments = fake.random_int(min=10, max=20)

    # Get some members
    members = db.query(Member).filter(Member.status == MemberStatus.ACTIVE).limit(50).all()

    if not members:
        print("  - No members found, skipping adjustments")
        return adjustments

    for _ in range(num_adjustments):
        member = fake.random_element(members)
        adj_type = fake.random_element(adjustment_types)

        # Determine amount based on type
        if adj_type == DuesAdjustmentType.LATE_FEE:
            amount = Decimal("25.00")  # Late fee charge
        elif adj_type == DuesAdjustmentType.CREDIT:
            amount = -Decimal(str(fake.random_int(min=10, max=75)))  # Credit (negative)
        elif adj_type in (DuesAdjustmentType.WAIVER, DuesAdjustmentType.HARDSHIP):
            amount = -Decimal(str(fake.random_int(min=25, max=75)))  # Reduction (negative)
        else:
            amount = Decimal(str(fake.random_int(min=-50, max=50)))

        # Link to payment if available
        member_payments = [p for p in payments if p.member_id == member.id]
        payment_id = fake.random_element(member_payments).id if member_payments else None

        # Determine status
        rand = fake.random_int(min=1, max=100)
        if rand <= 60:
            status = AdjustmentStatus.APPROVED
            approved_by_id = requestor_id
        elif rand <= 80:
            status = AdjustmentStatus.DENIED
            approved_by_id = requestor_id
        else:
            status = AdjustmentStatus.PENDING
            approved_by_id = None

        adjustment = DuesAdjustment(
            member_id=member.id,
            payment_id=payment_id,
            adjustment_type=adj_type,
            amount=amount,
            reason=fake.sentence(nb_words=10),
            status=status,
            requested_by_id=requestor_id,
            approved_by_id=approved_by_id,
            approved_at=fake.date_time_between(start_date="-30d", end_date="now") if approved_by_id else None
        )
        adjustments.append(adjustment)

    add_records(db, adjustments)
    print(f"  - Created {len(adjustments)} dues adjustments")
    return adjustments


def run_dues_seed(db: Session, verbose: bool = False):
    """Run all dues seeding functions."""
    if verbose:
        print("\n📊 Seeding Phase 4: Dues Tracking...")

    rates = seed_dues_rates(db)
    periods = seed_dues_periods(db)
    payments = seed_dues_payments(db, periods)
    adjustments = seed_dues_adjustments(db, payments)

    if verbose:
        print(f"✅ Dues seeding complete: {len(rates)} rates, {len(periods)} periods, {len(payments)} payments, {len(adjustments)} adjustments")

    return {
        "rates": len(rates),
        "periods": len(periods),
        "payments": len(payments),
        "adjustments": len(adjustments),
    }


if __name__ == "__main__":
    from src.db.session import get_db_session
    db = get_db_session()
    run_dues_seed(db, verbose=True)
