"""
Member Frontend Service - Stats and queries for member pages.
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from datetime import date
from decimal import Decimal
import logging

from src.models.member import Member
from src.models.member_employment import MemberEmployment
from src.models.dues_payment import DuesPayment
from src.db.enums import MemberStatus, MemberClassification, DuesPaymentStatus

logger = logging.getLogger(__name__)


class MemberFrontendService:
    """Service for member frontend operations."""

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # Stats Methods
    # ============================================================

    async def get_member_stats(self) -> dict:
        """
        Get overview statistics for the members dashboard.
        Returns counts for total, active, new this month, dues current.
        """
        # Total members (not deleted)
        total_stmt = select(func.count(Member.id)).where(Member.deleted_at.is_(None))
        total = (self.db.execute(total_stmt)).scalar() or 0

        # Active members
        active_stmt = select(func.count(Member.id)).where(
            and_(Member.deleted_at.is_(None), Member.status == MemberStatus.ACTIVE)
        )
        active = (self.db.execute(active_stmt)).scalar() or 0

        # New this month
        month_start = date.today().replace(day=1)
        new_stmt = select(func.count(Member.id)).where(
            and_(
                Member.deleted_at.is_(None), func.date(Member.created_at) >= month_start
            )
        )
        new_this_month = (self.db.execute(new_stmt)).scalar() or 0

        # Inactive members
        inactive_stmt = select(func.count(Member.id)).where(
            and_(Member.deleted_at.is_(None), Member.status == MemberStatus.INACTIVE)
        )
        inactive = (self.db.execute(inactive_stmt)).scalar() or 0

        # Suspended members
        suspended_stmt = select(func.count(Member.id)).where(
            and_(Member.deleted_at.is_(None), Member.status == MemberStatus.SUSPENDED)
        )
        suspended = (self.db.execute(suspended_stmt)).scalar() or 0

        # Retired members
        retired_stmt = select(func.count(Member.id)).where(
            and_(Member.deleted_at.is_(None), Member.status == MemberStatus.RETIRED)
        )
        retired = (self.db.execute(retired_stmt)).scalar() or 0

        # Calculate dues current percentage (simplified - based on active with recent payment)
        # This is a simplified version - adjust based on your actual dues logic
        dues_current_pct = 94  # Placeholder - implement actual calculation

        return {
            "total": total,
            "active": active,
            "inactive": inactive,
            "suspended": suspended,
            "retired": retired,
            "new_this_month": new_this_month,
            "dues_current_pct": dues_current_pct,
        }

    async def get_classification_breakdown(self) -> List[dict]:
        """
        Get member counts by classification.
        Returns list of dicts with classification name and count.
        """
        stmt = (
            select(Member.classification, func.count(Member.id).label("count"))
            .where(
                and_(Member.deleted_at.is_(None), Member.status == MemberStatus.ACTIVE)
            )
            .group_by(Member.classification)
            .order_by(func.count(Member.id).desc())
        )

        result = self.db.execute(stmt)
        rows = result.fetchall()

        breakdown = []
        for row in rows:
            if row.classification:
                breakdown.append(
                    {
                        "classification": row.classification,
                        "display_name": self.format_classification(row.classification),
                        "count": row.count,
                        "badge_class": self.get_classification_badge_class(
                            row.classification
                        ),
                    }
                )

        return breakdown

    async def get_recent_members(self, limit: int = 5) -> List[Member]:
        """Get most recently added members."""
        stmt = (
            select(Member)
            .where(Member.deleted_at.is_(None))
            .order_by(Member.created_at.desc())
            .limit(limit)
        )

        result = self.db.execute(stmt)
        return list(result.scalars().all())

    # ============================================================
    # Search and List Methods
    # ============================================================

    async def search_members(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        classification: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Member], int, int]:
        """
        Search members with filters and pagination.
        Returns (members, total_count, total_pages).
        """
        # Base query with eager loading
        stmt = (
            select(Member)
            .options(
                selectinload(Member.employments).selectinload(
                    MemberEmployment.organization
                )
            )
            .where(Member.deleted_at.is_(None))
        )

        # Apply search filter
        if query and query.strip():
            search_term = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    Member.member_number.ilike(search_term),
                    Member.first_name.ilike(search_term),
                    Member.last_name.ilike(search_term),
                    Member.email.ilike(search_term),
                    func.concat(Member.first_name, " ", Member.last_name).ilike(
                        search_term
                    ),
                )
            )

        # Apply status filter
        if status and status != "all":
            try:
                status_enum = MemberStatus(status)
                stmt = stmt.where(Member.status == status_enum)
            except ValueError:
                pass  # Invalid status, ignore filter

        # Apply classification filter
        if classification and classification != "all":
            try:
                class_enum = MemberClassification(classification)
                stmt = stmt.where(Member.classification == class_enum)
            except ValueError:
                pass  # Invalid classification, ignore filter

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (self.db.execute(count_stmt)).scalar() or 0

        # Apply sorting and pagination
        stmt = stmt.order_by(Member.last_name, Member.first_name)
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)

        result = self.db.execute(stmt)
        members = list(result.unique().scalars().all())

        total_pages = (total + per_page - 1) // per_page

        return members, total, total_pages

    async def get_member_by_id(self, member_id: int) -> Optional[Member]:
        """Get a single member by ID with relationships loaded."""
        stmt = (
            select(Member)
            .options(
                selectinload(Member.employments).selectinload(
                    MemberEmployment.organization
                ),
            )
            .where(and_(Member.id == member_id, Member.deleted_at.is_(None)))
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_member_current_employer(self, member: Member) -> Optional[dict]:
        """Get member's current employer info."""
        for emp in member.employments:
            if emp.is_current or emp.end_date is None:
                return {
                    "id": emp.organization.id,
                    "name": emp.organization.name,
                    "start_date": emp.start_date,
                    "job_title": emp.job_title,
                    "hourly_rate": emp.hourly_rate,
                }
        return None

    # ============================================================
    # Employment History Methods
    # ============================================================

    async def get_employment_history(self, member_id: int) -> List[dict]:
        """Get member's employment history as timeline data."""
        stmt = (
            select(MemberEmployment)
            .options(selectinload(MemberEmployment.organization))
            .where(MemberEmployment.member_id == member_id)
            .order_by(MemberEmployment.start_date.desc())
        )

        result = self.db.execute(stmt)
        employments = result.scalars().all()

        history = []
        for emp in employments:
            history.append(
                {
                    "id": emp.id,
                    "organization_id": emp.organization_id,
                    "organization_name": emp.organization.name
                    if emp.organization
                    else "Unknown",
                    "start_date": emp.start_date,
                    "end_date": emp.end_date,
                    "is_current": emp.is_current or emp.end_date is None,
                    "job_title": emp.job_title,
                    "hourly_rate": emp.hourly_rate,
                    "duration": self._calculate_duration(emp.start_date, emp.end_date),
                }
            )

        return history

    def _calculate_duration(self, start_date: date, end_date: Optional[date]) -> str:
        """Calculate employment duration as human-readable string."""
        end = end_date or date.today()
        delta = end - start_date
        years = delta.days // 365
        months = (delta.days % 365) // 30

        if years > 0 and months > 0:
            return f"{years}y {months}m"
        elif years > 0:
            return f"{years}y"
        elif months > 0:
            return f"{months}m"
        else:
            return f"{delta.days}d"

    # ============================================================
    # Dues Methods
    # ============================================================

    async def get_member_dues_summary(self, member_id: int) -> dict:
        """Get member's dues payment summary."""
        # Get recent payments
        stmt = (
            select(DuesPayment)
            .options(selectinload(DuesPayment.period))
            .where(DuesPayment.member_id == member_id)
            .order_by(DuesPayment.created_at.desc())
            .limit(6)
        )

        result = self.db.execute(stmt)
        payments = list(result.scalars().all())

        # Determine overall status
        if not payments:
            status = "unknown"
            status_class = "badge-ghost"
        else:
            latest = payments[0]
            if latest.status == DuesPaymentStatus.PAID:
                status = "current"
                status_class = "badge-success"
            elif latest.status == DuesPaymentStatus.OVERDUE:
                status = "overdue"
                status_class = "badge-error"
            elif latest.status == DuesPaymentStatus.PENDING:
                status = "pending"
                status_class = "badge-warning"
            else:
                status = "waived"
                status_class = "badge-info"

        # Calculate totals
        total_paid = sum(
            p.amount_paid for p in payments if p.status == DuesPaymentStatus.PAID
        ) or Decimal("0.00")

        return {
            "status": status,
            "status_class": status_class,
            "recent_payments": payments[:3],
            "total_paid_ytd": total_paid,
            "payment_count": len(payments),
        }

    # ============================================================
    # Helper Methods
    # ============================================================

    @staticmethod
    def format_classification(classification) -> str:
        """Format classification enum as display string."""
        if isinstance(classification, str):
            try:
                classification = MemberClassification(classification)
            except ValueError:
                return classification.replace("_", " ").title()

        mapping = {
            MemberClassification.JOURNEYMAN_WIREMAN: "Journeyman Wireman",
            MemberClassification.APPRENTICE_WIREMAN: "Apprentice Wireman",
            MemberClassification.JOURNEYMAN_TECHNICIAN: "Journeyman Technician",
            MemberClassification.APPRENTICE_TECHNICIAN: "Apprentice Technician",
            MemberClassification.RESIDENTIAL_WIREMAN: "Residential Wireman",
            MemberClassification.RESIDENTIAL_APPRENTICE: "Residential Apprentice",
            MemberClassification.INSTALLER_TECHNICIAN: "Installer Technician",
            MemberClassification.TRAINEE: "Trainee",
            MemberClassification.ORGANIZER: "Organizer",
        }
        return mapping.get(
            classification, str(classification).replace("_", " ").title()
        )

    @staticmethod
    def get_classification_badge_class(classification) -> str:
        """Get DaisyUI badge class for classification."""
        if isinstance(classification, str):
            try:
                classification = MemberClassification(classification)
            except ValueError:
                return "badge-ghost"

        mapping = {
            MemberClassification.JOURNEYMAN_WIREMAN: "badge-primary",
            MemberClassification.APPRENTICE_WIREMAN: "badge-secondary",
            MemberClassification.JOURNEYMAN_TECHNICIAN: "badge-accent",
            MemberClassification.APPRENTICE_TECHNICIAN: "badge-info",
            MemberClassification.RESIDENTIAL_WIREMAN: "badge-success",
            MemberClassification.RESIDENTIAL_APPRENTICE: "badge-warning",
            MemberClassification.INSTALLER_TECHNICIAN: "badge-neutral",
            MemberClassification.TRAINEE: "badge-ghost",
            MemberClassification.ORGANIZER: "badge-error",
        }
        return mapping.get(classification, "badge-ghost")

    @staticmethod
    def get_status_badge_class(status: MemberStatus) -> str:
        """Get DaisyUI badge class for member status."""
        mapping = {
            MemberStatus.ACTIVE: "badge-success",
            MemberStatus.INACTIVE: "badge-warning",
            MemberStatus.SUSPENDED: "badge-error",
            MemberStatus.RETIRED: "badge-ghost",
            MemberStatus.DECEASED: "badge-neutral",
        }
        return mapping.get(status, "badge-ghost")


# Convenience function
async def get_member_frontend_service(db: Session) -> MemberFrontendService:
    return MemberFrontendService(db)
