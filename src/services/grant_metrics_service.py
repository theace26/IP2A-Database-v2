"""Grant metrics and reporting service for compliance tracking."""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, and_, select
from sqlalchemy.orm import Session

from src.models import Grant, Expense
from src.models.grant_enrollment import GrantEnrollment
from src.db.enums import GrantStatus, GrantEnrollmentStatus, GrantOutcome


class GrantMetricsService:
    """Service for calculating grant metrics and compliance data."""

    # Status badge colors for UI
    STATUS_COLORS = {
        GrantStatus.PENDING: "badge-warning",
        GrantStatus.ACTIVE: "badge-success",
        GrantStatus.COMPLETED: "badge-info",
        GrantStatus.CLOSED: "badge-ghost",
        GrantStatus.SUSPENDED: "badge-error",
    }

    # Enrollment status colors
    ENROLLMENT_STATUS_COLORS = {
        GrantEnrollmentStatus.ENROLLED: "badge-info",
        GrantEnrollmentStatus.ACTIVE: "badge-success",
        GrantEnrollmentStatus.COMPLETED: "badge-primary",
        GrantEnrollmentStatus.WITHDRAWN: "badge-warning",
        GrantEnrollmentStatus.DROPPED: "badge-error",
    }

    # Outcome colors
    OUTCOME_COLORS = {
        GrantOutcome.COMPLETED_PROGRAM: "badge-success",
        GrantOutcome.OBTAINED_CREDENTIAL: "badge-success",
        GrantOutcome.ENTERED_APPRENTICESHIP: "badge-primary",
        GrantOutcome.OBTAINED_EMPLOYMENT: "badge-primary",
        GrantOutcome.CONTINUED_EDUCATION: "badge-info",
        GrantOutcome.WITHDRAWN: "badge-warning",
        GrantOutcome.OTHER: "badge-ghost",
    }

    @staticmethod
    def get_status_badge_class(status: GrantStatus) -> str:
        """Get badge class for grant status."""
        return GrantMetricsService.STATUS_COLORS.get(status, "badge-ghost")

    @staticmethod
    def get_enrollment_status_badge_class(status: GrantEnrollmentStatus) -> str:
        """Get badge class for enrollment status."""
        return GrantMetricsService.ENROLLMENT_STATUS_COLORS.get(status, "badge-ghost")

    @staticmethod
    def get_outcome_badge_class(outcome: GrantOutcome) -> str:
        """Get badge class for outcome."""
        return GrantMetricsService.OUTCOME_COLORS.get(outcome, "badge-ghost")

    def __init__(self, db: Session):
        self.db = db

    def get_grant_summary(self, grant_id: int) -> Optional[dict]:
        """Get comprehensive summary for a grant."""
        grant = self.db.query(Grant).filter(
            Grant.id == grant_id,
            Grant.is_deleted == False
        ).first()

        if not grant:
            return None

        # Enrollment metrics
        enrollment_stats = self._get_enrollment_stats(grant_id)

        # Financial metrics
        financial_stats = self._get_financial_stats(grant)

        # Outcome metrics
        outcome_stats = self._get_outcome_stats(grant_id)

        # Progress toward targets
        progress = self._calculate_progress(enrollment_stats, outcome_stats, grant)

        return {
            "grant_id": grant_id,
            "grant_name": grant.name,
            "grant_number": grant.grant_number,
            "funder": grant.funding_source,
            "status": grant.status,
            "period": {
                "start": grant.start_date,
                "end": grant.end_date,
            },
            "reporting": {
                "frequency": grant.reporting_frequency,
                "next_due": grant.next_report_due,
            },
            "enrollment": enrollment_stats,
            "financials": financial_stats,
            "outcomes": outcome_stats,
            "targets": {
                "enrollment": grant.target_enrollment,
                "completion": grant.target_completion,
                "placement": grant.target_placement,
            },
            "progress": progress,
        }

    def _get_enrollment_stats(self, grant_id: int) -> dict:
        """Calculate enrollment statistics."""
        # Total enrolled
        total = self.db.query(func.count(GrantEnrollment.id)).filter(
            GrantEnrollment.grant_id == grant_id,
            GrantEnrollment.is_deleted == False
        ).scalar() or 0

        # Currently active
        active = self.db.query(func.count(GrantEnrollment.id)).filter(
            GrantEnrollment.grant_id == grant_id,
            GrantEnrollment.is_deleted == False,
            GrantEnrollment.status == GrantEnrollmentStatus.ACTIVE
        ).scalar() or 0

        # Completed
        completed = self.db.query(func.count(GrantEnrollment.id)).filter(
            GrantEnrollment.grant_id == grant_id,
            GrantEnrollment.is_deleted == False,
            GrantEnrollment.status == GrantEnrollmentStatus.COMPLETED
        ).scalar() or 0

        # Attrition (withdrawn + dropped)
        attrition = self.db.query(func.count(GrantEnrollment.id)).filter(
            GrantEnrollment.grant_id == grant_id,
            GrantEnrollment.is_deleted == False,
            GrantEnrollment.status.in_([
                GrantEnrollmentStatus.WITHDRAWN,
                GrantEnrollmentStatus.DROPPED
            ])
        ).scalar() or 0

        return {
            "total_enrolled": total,
            "currently_active": active,
            "completed": completed,
            "attrition": attrition,
            "retention_rate": (
                round((total - attrition) / total * 100, 1)
                if total > 0 else 0.0
            ),
        }

    def _get_financial_stats(self, grant: Grant) -> dict:
        """Calculate financial statistics."""
        # Sum approved expenses
        total_spent = self.db.query(
            func.coalesce(func.sum(Expense.total_price), Decimal("0"))
        ).filter(
            Expense.grant_id == grant.id,
            Expense.is_deleted == False
        ).scalar() or Decimal("0")

        return {
            "total_budget": float(grant.total_amount),
            "total_spent": float(total_spent),
            "remaining": float(grant.total_amount - total_spent),
            "utilization_rate": round(
                float(total_spent / grant.total_amount * 100), 1
            ) if grant.total_amount > 0 else 0.0,
        }

    def _get_outcome_stats(self, grant_id: int) -> dict:
        """Calculate outcome statistics."""
        # Get outcomes grouped by type
        result = self.db.query(
            GrantEnrollment.outcome,
            func.count(GrantEnrollment.id)
        ).filter(
            GrantEnrollment.grant_id == grant_id,
            GrantEnrollment.is_deleted == False,
            GrantEnrollment.outcome.isnot(None)
        ).group_by(GrantEnrollment.outcome).all()

        outcomes = {row[0].value: row[1] for row in result if row[0]}

        total_with_outcomes = sum(outcomes.values())

        # Placement = employment + apprenticeship
        placement_count = (
            outcomes.get("obtained_employment", 0) +
            outcomes.get("entered_apprenticeship", 0)
        )

        return {
            "by_outcome": outcomes,
            "total_with_outcomes": total_with_outcomes,
            "placement_count": placement_count,
        }

    def _calculate_progress(
        self,
        enrollment: dict,
        outcomes: dict,
        grant: Grant
    ) -> dict:
        """Calculate progress toward targets."""
        progress = {}

        if grant.target_enrollment and grant.target_enrollment > 0:
            progress["enrollment"] = round(
                enrollment["total_enrolled"] / grant.target_enrollment * 100, 1
            )

        if grant.target_completion and grant.target_completion > 0:
            progress["completion"] = round(
                enrollment["completed"] / grant.target_completion * 100, 1
            )

        if grant.target_placement and grant.target_placement > 0:
            progress["placement"] = round(
                outcomes["placement_count"] / grant.target_placement * 100, 1
            )

        return progress

    def get_all_grants_summary(self) -> list[dict]:
        """Get summary for all active grants."""
        grants = self.db.query(Grant).filter(
            Grant.is_deleted == False,
            Grant.is_active == True
        ).order_by(Grant.start_date.desc()).all()

        summaries = []
        for grant in grants:
            # Get enrollment count
            enrollment_count = self.db.query(func.count(GrantEnrollment.id)).filter(
                GrantEnrollment.grant_id == grant.id,
                GrantEnrollment.is_deleted == False
            ).scalar() or 0

            # Get expense total
            total_spent = self.db.query(
                func.coalesce(func.sum(Expense.total_price), Decimal("0"))
            ).filter(
                Expense.grant_id == grant.id,
                Expense.is_deleted == False
            ).scalar() or Decimal("0")

            summaries.append({
                "id": grant.id,
                "name": grant.name,
                "grant_number": grant.grant_number,
                "funding_source": grant.funding_source,
                "status": grant.status,
                "total_amount": float(grant.total_amount),
                "spent_amount": float(total_spent),
                "start_date": grant.start_date,
                "end_date": grant.end_date,
                "target_enrollment": grant.target_enrollment,
                "current_enrollment": enrollment_count,
                "is_active": grant.is_active,
            })

        return summaries

    def get_dashboard_stats(self) -> dict:
        """Get summary statistics for dashboard."""
        # Active grants count
        active_grants = self.db.query(func.count(Grant.id)).filter(
            Grant.is_deleted == False,
            Grant.status == GrantStatus.ACTIVE
        ).scalar() or 0

        # Total funding
        total_funding = self.db.query(
            func.coalesce(func.sum(Grant.total_amount), Decimal("0"))
        ).filter(
            Grant.is_deleted == False,
            Grant.status == GrantStatus.ACTIVE
        ).scalar() or Decimal("0")

        # Total enrolled across all active grants
        active_grant_ids = self.db.query(Grant.id).filter(
            Grant.is_deleted == False,
            Grant.status == GrantStatus.ACTIVE
        ).all()
        active_grant_ids = [g[0] for g in active_grant_ids]

        total_enrolled = 0
        if active_grant_ids:
            total_enrolled = self.db.query(func.count(GrantEnrollment.id)).filter(
                GrantEnrollment.grant_id.in_(active_grant_ids),
                GrantEnrollment.is_deleted == False
            ).scalar() or 0

        # Grants ending soon (within 90 days)
        from datetime import timedelta
        ending_soon = self.db.query(func.count(Grant.id)).filter(
            Grant.is_deleted == False,
            Grant.status == GrantStatus.ACTIVE,
            Grant.end_date.isnot(None),
            Grant.end_date <= date.today() + timedelta(days=90)
        ).scalar() or 0

        return {
            "active_grants": active_grants,
            "total_funding": float(total_funding),
            "total_enrolled": total_enrolled,
            "ending_soon": ending_soon,
        }
