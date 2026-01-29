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