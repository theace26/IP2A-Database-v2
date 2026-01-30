"""
Operations Frontend Service.

Provides stats and queries for the Union Operations frontend module.
Handles SALTing activities, Benevolence applications, and Grievances.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from src.db.enums import (
    BenevolenceReason,
    BenevolenceStatus,
    GrievanceStatus,
    GrievanceStep,
    SALTingActivityType,
    SALTingOutcome,
)
from src.models import (
    BenevolenceApplication,
    Grievance,
    Member,
    Organization,
    SALTingActivity,
)


class OperationsFrontendService:
    """Service for operations frontend queries."""

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # Overview Stats (Landing Page)
    # ============================================================

    async def get_overview_stats(self) -> dict:
        """Get stats for operations landing page."""
        # SALTing stats
        salting_total = await self._count_salting_total()
        salting_this_month = await self._count_salting_this_month()

        # Benevolence stats
        benevolence_pending = await self._count_benevolence_pending()
        benevolence_ytd_amount = await self._sum_benevolence_ytd()

        # Grievance stats
        grievances_open = await self._count_grievances_open()
        grievances_total = await self._count_grievances_total()

        return {
            "salting": {
                "total_activities": salting_total,
                "this_month": salting_this_month,
            },
            "benevolence": {
                "pending": benevolence_pending,
                "ytd_amount": benevolence_ytd_amount,
            },
            "grievances": {
                "open": grievances_open,
                "total": grievances_total,
            },
        }

    async def _count_salting_total(self) -> int:
        stmt = select(func.count(SALTingActivity.id)).where(
            SALTingActivity.is_deleted == False  # noqa: E712
        )
        return (self.db.execute(stmt)).scalar() or 0

    async def _count_salting_this_month(self) -> int:
        first_of_month = date.today().replace(day=1)
        stmt = select(func.count(SALTingActivity.id)).where(
            SALTingActivity.is_deleted == False,  # noqa: E712
            SALTingActivity.activity_date >= first_of_month,
        )
        return (self.db.execute(stmt)).scalar() or 0

    async def _count_benevolence_pending(self) -> int:
        stmt = select(func.count(BenevolenceApplication.id)).where(
            BenevolenceApplication.is_deleted == False,  # noqa: E712
            BenevolenceApplication.status.in_(
                [
                    BenevolenceStatus.SUBMITTED,
                    BenevolenceStatus.UNDER_REVIEW,
                ]
            ),
        )
        return (self.db.execute(stmt)).scalar() or 0

    async def _sum_benevolence_ytd(self) -> Decimal:
        first_of_year = date.today().replace(month=1, day=1)
        stmt = select(func.sum(BenevolenceApplication.approved_amount)).where(
            BenevolenceApplication.is_deleted == False,  # noqa: E712
            BenevolenceApplication.status == BenevolenceStatus.PAID,
            BenevolenceApplication.payment_date >= first_of_year,
        )
        return (self.db.execute(stmt)).scalar() or Decimal("0")

    async def _count_grievances_open(self) -> int:
        stmt = select(func.count(Grievance.id)).where(
            Grievance.is_deleted == False,  # noqa: E712
            Grievance.status.in_(
                [
                    GrievanceStatus.OPEN,
                    GrievanceStatus.INVESTIGATION,
                    GrievanceStatus.HEARING,
                    GrievanceStatus.ARBITRATION,
                ]
            ),
        )
        return (self.db.execute(stmt)).scalar() or 0

    async def _count_grievances_total(self) -> int:
        stmt = select(func.count(Grievance.id)).where(
            Grievance.is_deleted == False  # noqa: E712
        )
        return (self.db.execute(stmt)).scalar() or 0

    # ============================================================
    # SALTing Methods
    # ============================================================

    async def get_salting_stats(self) -> dict:
        """Get SALTing stats for list page."""
        total = await self._count_salting_total()
        this_month = await self._count_salting_this_month()
        workers_contacted = await self._sum_workers_contacted()
        cards_signed = await self._sum_cards_signed()

        # Count by outcome
        positive = await self._count_salting_by_outcome(SALTingOutcome.POSITIVE)
        neutral = await self._count_salting_by_outcome(SALTingOutcome.NEUTRAL)
        negative = await self._count_salting_by_outcome(SALTingOutcome.NEGATIVE)

        return {
            "total": total,
            "this_month": this_month,
            "workers_contacted": workers_contacted,
            "cards_signed": cards_signed,
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
        }

    async def _sum_workers_contacted(self) -> int:
        stmt = select(func.sum(SALTingActivity.workers_contacted)).where(
            SALTingActivity.is_deleted == False  # noqa: E712
        )
        return (self.db.execute(stmt)).scalar() or 0

    async def _sum_cards_signed(self) -> int:
        stmt = select(func.sum(SALTingActivity.cards_signed)).where(
            SALTingActivity.is_deleted == False  # noqa: E712
        )
        return (self.db.execute(stmt)).scalar() or 0

    async def _count_salting_by_outcome(self, outcome: SALTingOutcome) -> int:
        stmt = select(func.count(SALTingActivity.id)).where(
            SALTingActivity.is_deleted == False,  # noqa: E712
            SALTingActivity.outcome == outcome,
        )
        return (self.db.execute(stmt)).scalar() or 0

    async def search_salting_activities(
        self,
        query: Optional[str] = None,
        activity_type: Optional[str] = None,
        outcome: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[SALTingActivity], int, int]:
        """Search SALTing activities with filters."""
        stmt = (
            select(SALTingActivity)
            .options(
                selectinload(SALTingActivity.member),
                selectinload(SALTingActivity.organization),
            )
            .where(SALTingActivity.is_deleted == False)  # noqa: E712
        )

        # Search by member name or organization name
        if query and query.strip():
            search_term = f"%{query.strip()}%"
            stmt = stmt.outerjoin(SALTingActivity.member).outerjoin(
                SALTingActivity.organization
            )
            stmt = stmt.where(
                or_(
                    Member.first_name.ilike(search_term),
                    Member.last_name.ilike(search_term),
                    func.concat(Member.first_name, " ", Member.last_name).ilike(
                        search_term
                    ),
                    Organization.name.ilike(search_term),
                    SALTingActivity.location.ilike(search_term),
                )
            )

        # Filter by activity type
        if activity_type and activity_type != "all":
            try:
                type_enum = SALTingActivityType(activity_type)
                stmt = stmt.where(SALTingActivity.activity_type == type_enum)
            except ValueError:
                pass

        # Filter by outcome
        if outcome and outcome != "all":
            try:
                outcome_enum = SALTingOutcome(outcome)
                stmt = stmt.where(SALTingActivity.outcome == outcome_enum)
            except ValueError:
                pass

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (self.db.execute(count_stmt)).scalar() or 0

        # Sort and paginate
        stmt = stmt.order_by(SALTingActivity.activity_date.desc())
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)

        result = self.db.execute(stmt)
        activities = list(result.unique().scalars().all())

        total_pages = (total + per_page - 1) // per_page

        return activities, total, total_pages

    async def get_salting_activity_by_id(
        self, activity_id: int
    ) -> Optional[SALTingActivity]:
        """Get a SALTing activity with relationships."""
        stmt = (
            select(SALTingActivity)
            .options(
                selectinload(SALTingActivity.member),
                selectinload(SALTingActivity.organization),
            )
            .where(
                SALTingActivity.id == activity_id,
                SALTingActivity.is_deleted == False,  # noqa: E712
            )
        )

        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def get_salting_outcome_badge_class(outcome: Optional[SALTingOutcome]) -> str:
        """Get DaisyUI badge class for SALTing outcome."""
        if outcome is None:
            return "badge-ghost"
        mapping = {
            SALTingOutcome.POSITIVE: "badge-success",
            SALTingOutcome.NEUTRAL: "badge-warning",
            SALTingOutcome.NEGATIVE: "badge-error",
            SALTingOutcome.NO_CONTACT: "badge-ghost",
        }
        return mapping.get(outcome, "badge-ghost")

    @staticmethod
    def get_salting_type_badge_class(activity_type: SALTingActivityType) -> str:
        """Get DaisyUI badge class for activity type."""
        mapping = {
            SALTingActivityType.OUTREACH: "badge-primary",
            SALTingActivityType.SITE_VISIT: "badge-secondary",
            SALTingActivityType.LEAFLETING: "badge-accent",
            SALTingActivityType.ONE_ON_ONE: "badge-info",
            SALTingActivityType.MEETING: "badge-success",
            SALTingActivityType.PETITION_DRIVE: "badge-warning",
            SALTingActivityType.CARD_SIGNING: "badge-error",
            SALTingActivityType.INFORMATION_SESSION: "badge-primary",
            SALTingActivityType.OTHER: "badge-ghost",
        }
        return mapping.get(activity_type, "badge-ghost")

    # ============================================================
    # Benevolence Methods
    # ============================================================

    async def get_benevolence_stats(self) -> dict:
        """Get benevolence stats for list page."""
        total = await self._count_benevolence_total()
        pending = await self._count_benevolence_pending()
        approved = await self._count_benevolence_by_status(BenevolenceStatus.APPROVED)
        paid = await self._count_benevolence_by_status(BenevolenceStatus.PAID)
        ytd_amount = await self._sum_benevolence_ytd()

        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "paid": paid,
            "ytd_amount": ytd_amount,
        }

    async def _count_benevolence_total(self) -> int:
        stmt = select(func.count(BenevolenceApplication.id)).where(
            BenevolenceApplication.is_deleted == False  # noqa: E712
        )
        return (self.db.execute(stmt)).scalar() or 0

    async def _count_benevolence_by_status(self, status: BenevolenceStatus) -> int:
        stmt = select(func.count(BenevolenceApplication.id)).where(
            BenevolenceApplication.is_deleted == False,  # noqa: E712
            BenevolenceApplication.status == status,
        )
        return (self.db.execute(stmt)).scalar() or 0

    async def search_benevolence_applications(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[BenevolenceApplication], int, int]:
        """Search benevolence applications with filters."""
        stmt = (
            select(BenevolenceApplication)
            .options(
                selectinload(BenevolenceApplication.member),
                selectinload(BenevolenceApplication.reviews),
            )
            .where(BenevolenceApplication.is_deleted == False)  # noqa: E712
        )

        # Search by member name
        if query and query.strip():
            search_term = f"%{query.strip()}%"
            stmt = stmt.outerjoin(BenevolenceApplication.member)
            stmt = stmt.where(
                or_(
                    Member.first_name.ilike(search_term),
                    Member.last_name.ilike(search_term),
                    func.concat(Member.first_name, " ", Member.last_name).ilike(
                        search_term
                    ),
                )
            )

        # Filter by status
        if status and status != "all":
            try:
                status_enum = BenevolenceStatus(status)
                stmt = stmt.where(BenevolenceApplication.status == status_enum)
            except ValueError:
                pass

        # Filter by reason
        if reason and reason != "all":
            try:
                reason_enum = BenevolenceReason(reason)
                stmt = stmt.where(BenevolenceApplication.reason == reason_enum)
            except ValueError:
                pass

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (self.db.execute(count_stmt)).scalar() or 0

        # Sort and paginate
        stmt = stmt.order_by(BenevolenceApplication.application_date.desc())
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)

        result = self.db.execute(stmt)
        applications = list(result.unique().scalars().all())

        total_pages = (total + per_page - 1) // per_page

        return applications, total, total_pages

    async def get_benevolence_application_by_id(
        self, application_id: int
    ) -> Optional[BenevolenceApplication]:
        """Get a benevolence application with relationships."""
        stmt = (
            select(BenevolenceApplication)
            .options(
                selectinload(BenevolenceApplication.member),
                selectinload(BenevolenceApplication.reviews),
            )
            .where(
                BenevolenceApplication.id == application_id,
                BenevolenceApplication.is_deleted == False,  # noqa: E712
            )
        )

        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def get_benevolence_status_badge_class(status: BenevolenceStatus) -> str:
        """Get DaisyUI badge class for benevolence status."""
        mapping = {
            BenevolenceStatus.DRAFT: "badge-ghost",
            BenevolenceStatus.SUBMITTED: "badge-info",
            BenevolenceStatus.UNDER_REVIEW: "badge-warning",
            BenevolenceStatus.APPROVED: "badge-success",
            BenevolenceStatus.DENIED: "badge-error",
            BenevolenceStatus.PAID: "badge-primary",
        }
        return mapping.get(status, "badge-ghost")

    @staticmethod
    def get_benevolence_reason_badge_class(reason: BenevolenceReason) -> str:
        """Get DaisyUI badge class for benevolence reason."""
        mapping = {
            BenevolenceReason.MEDICAL: "badge-error",
            BenevolenceReason.DEATH_IN_FAMILY: "badge-secondary",
            BenevolenceReason.HARDSHIP: "badge-warning",
            BenevolenceReason.DISASTER: "badge-accent",
            BenevolenceReason.OTHER: "badge-ghost",
        }
        return mapping.get(reason, "badge-ghost")

    # ============================================================
    # Grievance Methods
    # ============================================================

    async def get_grievance_stats(self) -> dict:
        """Get grievance stats for list page."""
        total = await self._count_grievances_total()
        open_count = await self._count_grievances_open()

        # Count by step
        step1 = await self._count_grievances_by_step(GrievanceStep.STEP_1)
        step2 = await self._count_grievances_by_step(GrievanceStep.STEP_2)
        step3 = await self._count_grievances_by_step(GrievanceStep.STEP_3)
        arbitration = await self._count_grievances_by_step(GrievanceStep.ARBITRATION)

        # Count resolved
        settled = await self._count_grievances_by_status(GrievanceStatus.SETTLED)
        closed = await self._count_grievances_by_status(GrievanceStatus.CLOSED)
        resolved = settled + closed

        # Resolution rate
        resolution_rate = (resolved / total * 100) if total > 0 else 0

        return {
            "total": total,
            "open": open_count,
            "step_1": step1,
            "step_2": step2,
            "step_3": step3,
            "arbitration": arbitration,
            "resolved": resolved,
            "resolution_rate": round(resolution_rate, 1),
        }

    async def _count_grievances_by_step(self, step: GrievanceStep) -> int:
        stmt = select(func.count(Grievance.id)).where(
            Grievance.is_deleted == False,  # noqa: E712
            Grievance.current_step == step,
        )
        return (self.db.execute(stmt)).scalar() or 0

    async def _count_grievances_by_status(self, status: GrievanceStatus) -> int:
        stmt = select(func.count(Grievance.id)).where(
            Grievance.is_deleted == False,  # noqa: E712
            Grievance.status == status,
        )
        return (self.db.execute(stmt)).scalar() or 0

    async def search_grievances(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        step: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Grievance], int, int]:
        """Search grievances with filters."""
        stmt = (
            select(Grievance)
            .options(
                selectinload(Grievance.member),
                selectinload(Grievance.employer),
            )
            .where(Grievance.is_deleted == False)  # noqa: E712
        )

        # Search by grievance number, member name, or employer
        if query and query.strip():
            search_term = f"%{query.strip()}%"
            stmt = stmt.outerjoin(Grievance.member).outerjoin(Grievance.employer)
            stmt = stmt.where(
                or_(
                    Grievance.grievance_number.ilike(search_term),
                    Member.first_name.ilike(search_term),
                    Member.last_name.ilike(search_term),
                    func.concat(Member.first_name, " ", Member.last_name).ilike(
                        search_term
                    ),
                    Organization.name.ilike(search_term),
                    Grievance.violation_description.ilike(search_term),
                )
            )

        # Filter by status
        if status and status != "all":
            try:
                status_enum = GrievanceStatus(status)
                stmt = stmt.where(Grievance.status == status_enum)
            except ValueError:
                pass

        # Filter by step
        if step and step != "all":
            try:
                step_enum = GrievanceStep(step)
                stmt = stmt.where(Grievance.current_step == step_enum)
            except ValueError:
                pass

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (self.db.execute(count_stmt)).scalar() or 0

        # Sort and paginate
        stmt = stmt.order_by(Grievance.filed_date.desc())
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)

        result = self.db.execute(stmt)
        grievances = list(result.unique().scalars().all())

        total_pages = (total + per_page - 1) // per_page

        return grievances, total, total_pages

    async def get_grievance_by_id(self, grievance_id: int) -> Optional[Grievance]:
        """Get a grievance with all relationships."""
        stmt = (
            select(Grievance)
            .options(
                selectinload(Grievance.member),
                selectinload(Grievance.employer),
                selectinload(Grievance.steps),
            )
            .where(
                Grievance.id == grievance_id,
                Grievance.is_deleted == False,  # noqa: E712
            )
        )

        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def get_grievance_status_badge_class(status: GrievanceStatus) -> str:
        """Get DaisyUI badge class for grievance status."""
        mapping = {
            GrievanceStatus.OPEN: "badge-info",
            GrievanceStatus.INVESTIGATION: "badge-warning",
            GrievanceStatus.HEARING: "badge-accent",
            GrievanceStatus.SETTLED: "badge-success",
            GrievanceStatus.WITHDRAWN: "badge-ghost",
            GrievanceStatus.ARBITRATION: "badge-error",
            GrievanceStatus.CLOSED: "badge-neutral",
        }
        return mapping.get(status, "badge-ghost")

    @staticmethod
    def get_grievance_step_badge_class(step: GrievanceStep) -> str:
        """Get DaisyUI badge class for grievance step."""
        mapping = {
            GrievanceStep.STEP_1: "badge-info",
            GrievanceStep.STEP_2: "badge-warning",
            GrievanceStep.STEP_3: "badge-error",
            GrievanceStep.ARBITRATION: "badge-secondary",
        }
        return mapping.get(step, "badge-ghost")
