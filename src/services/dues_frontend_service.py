"""Frontend service for dues management UI."""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from src.models import DuesRate, DuesPeriod, DuesPayment, DuesAdjustment, Member
from src.db.enums import (
    MemberClassification,
    DuesPaymentStatus,
    DuesPaymentMethod,
    DuesAdjustmentType,
    AdjustmentStatus,
)


class DuesFrontendService:
    """Service for dues frontend operations."""

    # Classification badge colors
    CLASSIFICATION_COLORS = {
        MemberClassification.JOURNEYMAN: "badge-primary",
        MemberClassification.APPRENTICE_1ST_YEAR: "badge-secondary",
        MemberClassification.APPRENTICE_2ND_YEAR: "badge-secondary",
        MemberClassification.APPRENTICE_3RD_YEAR: "badge-secondary",
        MemberClassification.APPRENTICE_4TH_YEAR: "badge-secondary",
        MemberClassification.APPRENTICE_5TH_YEAR: "badge-secondary",
        MemberClassification.FOREMAN: "badge-accent",
        MemberClassification.RETIREE: "badge-ghost",
        MemberClassification.HONORARY: "badge-ghost",
    }

    # Payment status badge colors
    PAYMENT_STATUS_COLORS = {
        DuesPaymentStatus.PENDING: "badge-warning",
        DuesPaymentStatus.PAID: "badge-success",
        DuesPaymentStatus.PARTIAL: "badge-info",
        DuesPaymentStatus.OVERDUE: "badge-error",
        DuesPaymentStatus.WAIVED: "badge-ghost",
    }

    # Adjustment status badge colors
    ADJUSTMENT_STATUS_COLORS = {
        AdjustmentStatus.PENDING: "badge-warning",
        AdjustmentStatus.APPROVED: "badge-success",
        AdjustmentStatus.DENIED: "badge-error",
    }

    # Adjustment type badge colors
    ADJUSTMENT_TYPE_COLORS = {
        DuesAdjustmentType.WAIVER: "badge-info",
        DuesAdjustmentType.CREDIT: "badge-success",
        DuesAdjustmentType.HARDSHIP: "badge-warning",
        DuesAdjustmentType.CORRECTION: "badge-secondary",
        DuesAdjustmentType.OTHER: "badge-ghost",
    }

    @staticmethod
    def get_classification_badge_class(classification: MemberClassification) -> str:
        """Get badge class for member classification."""
        return DuesFrontendService.CLASSIFICATION_COLORS.get(classification, "badge-ghost")

    @staticmethod
    def get_payment_status_badge_class(status: DuesPaymentStatus) -> str:
        """Get badge class for payment status."""
        return DuesFrontendService.PAYMENT_STATUS_COLORS.get(status, "badge-ghost")

    @staticmethod
    def get_adjustment_status_badge_class(status: AdjustmentStatus) -> str:
        """Get badge class for adjustment status."""
        return DuesFrontendService.ADJUSTMENT_STATUS_COLORS.get(status, "badge-ghost")

    @staticmethod
    def get_adjustment_type_badge_class(adj_type: DuesAdjustmentType) -> str:
        """Get badge class for adjustment type."""
        return DuesFrontendService.ADJUSTMENT_TYPE_COLORS.get(adj_type, "badge-ghost")

    @staticmethod
    def get_landing_stats(db: Session) -> dict:
        """Get stats for dues landing page."""
        today = date.today()
        current_month_start = today.replace(day=1)
        current_year_start = today.replace(month=1, day=1)

        # Current period - find open period
        current_period = (
            db.query(DuesPeriod)
            .filter(DuesPeriod.is_closed == False)  # noqa: E712
            .order_by(DuesPeriod.period_year.desc(), DuesPeriod.period_month.desc())
            .first()
        )

        # MTD collections
        mtd_collected = (
            db.query(func.coalesce(func.sum(DuesPayment.amount_paid), Decimal("0")))
            .filter(
                and_(
                    DuesPayment.payment_date >= current_month_start,
                    DuesPayment.payment_date <= today,
                )
            )
            .scalar()
        ) or Decimal("0")

        # YTD collections
        ytd_collected = (
            db.query(func.coalesce(func.sum(DuesPayment.amount_paid), Decimal("0")))
            .filter(
                and_(
                    DuesPayment.payment_date >= current_year_start,
                    DuesPayment.payment_date <= today,
                )
            )
            .scalar()
        ) or Decimal("0")

        # Overdue count
        overdue_count = (
            db.query(func.count(DuesPayment.id))
            .filter(DuesPayment.status == DuesPaymentStatus.OVERDUE)
            .scalar()
        ) or 0

        # Pending adjustments
        pending_adjustments = (
            db.query(func.count(DuesAdjustment.id))
            .filter(DuesAdjustment.status == AdjustmentStatus.PENDING)
            .scalar()
        ) or 0

        # Active rates count
        active_rates = (
            db.query(func.count(DuesRate.id))
            .filter(
                and_(
                    DuesRate.effective_date <= today,
                    or_(DuesRate.end_date == None, DuesRate.end_date >= today),  # noqa: E711
                )
            )
            .scalar()
        ) or 0

        # Days until due
        days_until_due = None
        if current_period and current_period.due_date:
            if current_period.due_date >= today:
                days_until_due = (current_period.due_date - today).days
            else:
                days_until_due = -(today - current_period.due_date).days

        return {
            "current_period": current_period,
            "days_until_due": days_until_due,
            "mtd_collected": mtd_collected,
            "ytd_collected": ytd_collected,
            "overdue_count": overdue_count,
            "pending_adjustments": pending_adjustments,
            "active_rates": active_rates,
        }

    @staticmethod
    def get_all_rates(
        db: Session,
        classification: Optional[MemberClassification] = None,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[DuesRate], int]:
        """Get all rates with optional filtering."""
        today = date.today()
        query = db.query(DuesRate)

        if classification:
            query = query.filter(DuesRate.classification == classification)

        if active_only:
            query = query.filter(
                and_(
                    DuesRate.effective_date <= today,
                    or_(DuesRate.end_date == None, DuesRate.end_date >= today),  # noqa: E711
                )
            )

        total = query.count()
        rates = (
            query.order_by(DuesRate.classification, DuesRate.effective_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return rates, total

    @staticmethod
    def format_currency(amount: Optional[Decimal]) -> str:
        """Format decimal as currency string."""
        if amount is None:
            return "$0.00"
        return f"${float(amount):,.2f}"

    @staticmethod
    def format_period_name(period: DuesPeriod) -> str:
        """Format period as readable name."""
        month_names = [
            "", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        return f"{month_names[period.period_month]} {period.period_year}"

    @staticmethod
    def get_all_periods(
        db: Session,
        year: Optional[int] = None,
        is_closed: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[DuesPeriod], int]:
        """Get all periods with optional filtering."""
        query = db.query(DuesPeriod)

        if year:
            query = query.filter(DuesPeriod.period_year == year)

        if is_closed is not None:
            query = query.filter(DuesPeriod.is_closed == is_closed)

        total = query.count()

        periods = (
            query.order_by(
                DuesPeriod.period_year.desc(),
                DuesPeriod.period_month.desc(),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        return periods, total

    @staticmethod
    def get_period_with_stats(db: Session, period_id: int) -> Optional[dict]:
        """Get period with payment statistics."""
        period = db.query(DuesPeriod).filter(DuesPeriod.id == period_id).first()
        if not period:
            return None

        # Get payment stats for this period
        payments = (
            db.query(DuesPayment)
            .filter(DuesPayment.period_id == period_id)
            .all()
        )

        total_due = sum(p.amount_due for p in payments) if payments else Decimal("0")
        total_paid = sum(p.amount_paid or Decimal("0") for p in payments) if payments else Decimal("0")

        status_counts = {}
        for payment in payments:
            status = payment.status
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "period": period,
            "total_members": len(payments),
            "total_due": total_due,
            "total_paid": total_paid,
            "collection_rate": (
                (total_paid / total_due * 100) if total_due > 0 else Decimal("0")
            ),
            "status_counts": status_counts,
            "payments": payments[:20],  # First 20 for display
        }

    @staticmethod
    def get_available_years(db: Session) -> list[int]:
        """Get list of years that have periods."""
        years = (
            db.query(DuesPeriod.period_year)
            .distinct()
            .order_by(DuesPeriod.period_year.desc())
            .all()
        )
        return [y[0] for y in years]

    @staticmethod
    def get_period_status_badge_class(period: DuesPeriod) -> str:
        """Get badge class for period status."""
        if period.is_closed:
            return "badge-ghost"

        today = date.today()
        if period.grace_period_end and today > period.grace_period_end:
            return "badge-error"  # Past grace period
        elif period.due_date and today > period.due_date:
            return "badge-warning"  # Past due, in grace
        else:
            return "badge-success"  # Current/upcoming

    @staticmethod
    def get_period_status_text(period: DuesPeriod) -> str:
        """Get status text for period."""
        if period.is_closed:
            return "Closed"

        today = date.today()
        if period.grace_period_end and today > period.grace_period_end:
            return "Past Grace"
        elif period.due_date and today > period.due_date:
            return "In Grace Period"
        elif period.due_date and today == period.due_date:
            return "Due Today"
        else:
            return "Open"

    @staticmethod
    def get_all_payments(
        db: Session,
        period_id: Optional[int] = None,
        member_id: Optional[int] = None,
        status: Optional[DuesPaymentStatus] = None,
        q: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[DuesPayment], int]:
        """Get all payments with optional filtering."""
        query = db.query(DuesPayment).join(DuesPayment.member, isouter=True)

        if period_id:
            query = query.filter(DuesPayment.period_id == period_id)

        if member_id:
            query = query.filter(DuesPayment.member_id == member_id)

        if status:
            query = query.filter(DuesPayment.status == status)

        if q:
            search = f"%{q}%"
            query = query.filter(
                (Member.first_name.ilike(search))
                | (Member.last_name.ilike(search))
                | (Member.member_number.ilike(search))
            )

        total = query.count()

        payments = (
            query.order_by(DuesPayment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return payments, total

    @staticmethod
    def get_member_payment_summary(db: Session, member_id: int) -> dict:
        """Get payment summary for a member."""
        payments = (
            db.query(DuesPayment)
            .filter(DuesPayment.member_id == member_id)
            .order_by(DuesPayment.created_at.desc())
            .all()
        )

        total_due = sum(p.amount_due for p in payments) if payments else Decimal("0")
        total_paid = sum(p.amount_paid or Decimal("0") for p in payments) if payments else Decimal("0")

        status_counts = {}
        for payment in payments:
            status = payment.status
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "payments": payments,
            "total_due": total_due,
            "total_paid": total_paid,
            "balance": total_due - total_paid,
            "status_counts": status_counts,
            "payment_count": len(payments),
        }

    @staticmethod
    def get_all_adjustments(
        db: Session,
        status: Optional[AdjustmentStatus] = None,
        adjustment_type: Optional[DuesAdjustmentType] = None,
        member_id: Optional[int] = None,
        q: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[DuesAdjustment], int]:
        """Get all adjustments with optional filtering."""
        query = db.query(DuesAdjustment).join(DuesAdjustment.member, isouter=True)

        if status:
            query = query.filter(DuesAdjustment.status == status)

        if adjustment_type:
            query = query.filter(DuesAdjustment.adjustment_type == adjustment_type)

        if member_id:
            query = query.filter(DuesAdjustment.member_id == member_id)

        if q:
            search = f"%{q}%"
            query = query.filter(
                (Member.first_name.ilike(search))
                | (Member.last_name.ilike(search))
                | (Member.member_number.ilike(search))
                | (DuesAdjustment.reason.ilike(search))
            )

        total = query.count()

        adjustments = (
            query.order_by(DuesAdjustment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return adjustments, total

    @staticmethod
    def get_adjustment_detail(db: Session, adjustment_id: int) -> Optional[DuesAdjustment]:
        """Get adjustment with related data."""
        return (
            db.query(DuesAdjustment)
            .filter(DuesAdjustment.id == adjustment_id)
            .first()
        )

    @staticmethod
    def get_payment_method_display(method: Optional[DuesPaymentMethod]) -> str:
        """Get display name for payment method."""
        if not method:
            return "—"
        display_names = {
            DuesPaymentMethod.CASH: "Cash",
            DuesPaymentMethod.CHECK: "Check",
            DuesPaymentMethod.CREDIT_CARD: "Credit Card",
            DuesPaymentMethod.MONEY_ORDER: "Money Order",
            DuesPaymentMethod.ACH_TRANSFER: "ACH Transfer",
            DuesPaymentMethod.PAYROLL_DEDUCTION: "Payroll Deduction",
            DuesPaymentMethod.ONLINE: "Online",
            # Stripe payment methods
            DuesPaymentMethod.STRIPE_CARD: "Stripe (Card)",
            DuesPaymentMethod.STRIPE_ACH: "Stripe (ACH)",
            DuesPaymentMethod.STRIPE_OTHER: "Stripe (Other)",
            DuesPaymentMethod.OTHER: "Other",
        }
        return display_names.get(method, method.value)

    @staticmethod
    def get_rate_for_member(db: Session, member_id: int) -> Optional[DuesRate]:
        """
        Get the active dues rate for a member's classification.

        Args:
            db: Database session
            member_id: Member ID

        Returns:
            DuesRate object for the member's classification, or None if not found
        """
        # Get member
        member = db.query(Member).filter(Member.id == member_id).first()
        if not member:
            return None

        # Get active rate for member's classification
        today = date.today()

        rate = (
            db.query(DuesRate)
            .filter(
                and_(
                    DuesRate.classification == member.classification,
                    DuesRate.effective_date <= today,
                    or_(
                        DuesRate.end_date.is_(None),
                        DuesRate.end_date >= today
                    )
                )
            )
            .order_by(DuesRate.effective_date.desc())
            .first()
        )

        return rate