"""
Dashboard Service - Aggregates stats from multiple modules.
Optimized for quick dashboard loading.
"""

from datetime import datetime
from typing import Any, Dict, List
import logging

from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from src.models.member import Member
from src.models.student import Student
from src.models.grievance import Grievance
from src.models.dues_payment import DuesPayment
from src.models.audit_log import AuditLog
from src.models.labor_request import LaborRequest
from src.models.book_registration import BookRegistration
from src.models.certification import Certification
from src.db.enums import (
    MemberStatus,
    StudentStatus,
    GrievanceStatus,
    DuesPaymentStatus,
    LaborRequestStatus,
    RegistrationStatus,
    CertificationStatus,
)

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard data aggregation."""

    def __init__(self, db: Session):
        self.db = db

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get all dashboard statistics.
        Uses efficient COUNT queries instead of loading all records.
        """
        stats = {}

        try:
            # Active members count
            stats["active_members"] = self._count_active_members()
            stats["members_change"] = self._get_members_change_this_month()

            # Active students count
            stats["active_students"] = self._count_active_students()

            # Pending grievances
            stats["pending_grievances"] = self._count_pending_grievances()

            # Dues collected this month
            stats["dues_mtd"] = self._get_dues_mtd()

            # Open dispatch requests
            stats["open_dispatch_requests"] = self._count_open_dispatch_requests()

            # Members on referral books
            stats["members_on_book"] = self._count_members_on_book()

            # Upcoming certification expirations
            stats["upcoming_expirations"] = self._count_upcoming_expirations()

        except Exception as e:
            logger.error(f"Error fetching dashboard stats: {e}")
            # Return zeros on error to prevent dashboard crash
            stats = {
                "active_members": 0,
                "members_change": "+0",
                "active_students": 0,
                "pending_grievances": 0,
                "dues_mtd": 0,
                "open_dispatch_requests": 0,
                "members_on_book": 0,
                "upcoming_expirations": 0,
            }

        return stats

    def _count_active_members(self) -> int:
        """Count members with active status."""
        result = self.db.execute(
            select(func.count(Member.id)).where(Member.status == MemberStatus.ACTIVE)
        )
        return result.scalar() or 0

    def _get_members_change_this_month(self) -> str:
        """Get net member change this month."""
        first_of_month = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # Count members created this month
        result = self.db.execute(
            select(func.count(Member.id)).where(
                and_(
                    Member.created_at >= first_of_month,
                    Member.status == MemberStatus.ACTIVE,
                )
            )
        )
        new_members = result.scalar() or 0

        # Format with sign
        if new_members > 0:
            return f"+{new_members}"
        return str(new_members)

    def _count_active_students(self) -> int:
        """Count students with active enrollment."""
        result = self.db.execute(
            select(func.count(Student.id)).where(
                Student.status == StudentStatus.ENROLLED
            )
        )
        return result.scalar() or 0

    def _count_pending_grievances(self) -> int:
        """Count grievances in open/investigation/hearing status."""
        pending_statuses = [
            GrievanceStatus.OPEN,
            GrievanceStatus.INVESTIGATION,
            GrievanceStatus.HEARING,
            GrievanceStatus.ARBITRATION,
        ]
        result = self.db.execute(
            select(func.count(Grievance.id)).where(
                Grievance.status.in_(pending_statuses)
            )
        )
        return result.scalar() or 0

    def _get_dues_mtd(self) -> float:
        """Get total dues collected this month."""
        first_of_month = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        result = self.db.execute(
            select(func.coalesce(func.sum(DuesPayment.amount_paid), 0)).where(
                and_(
                    DuesPayment.payment_date >= first_of_month.date(),
                    DuesPayment.status == DuesPaymentStatus.PAID,
                )
            )
        )
        return float(result.scalar() or 0)

    def _count_open_dispatch_requests(self) -> int:
        """Count labor requests with open or partially filled status."""
        open_statuses = [
            LaborRequestStatus.OPEN,
            LaborRequestStatus.PARTIALLY_FILLED,
        ]
        result = self.db.execute(
            select(func.count(LaborRequest.id)).where(
                LaborRequest.status.in_(open_statuses)
            )
        )
        return result.scalar() or 0

    def _count_members_on_book(self) -> int:
        """Count active registrations across all referral books."""
        result = self.db.execute(
            select(func.count(BookRegistration.id)).where(
                BookRegistration.status == RegistrationStatus.REGISTERED
            )
        )
        return result.scalar() or 0

    def _count_upcoming_expirations(self, days: int = 30) -> int:
        """Count certifications expiring within N days."""
        from datetime import date, timedelta

        today = date.today()
        cutoff = today + timedelta(days=days)

        result = self.db.execute(
            select(func.count(Certification.id)).where(
                and_(
                    Certification.status == CertificationStatus.ACTIVE,
                    Certification.expiration_date.isnot(None),
                    Certification.expiration_date >= today,
                    Certification.expiration_date <= cutoff,
                )
            )
        )
        return result.scalar() or 0

    async def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent activity from audit log.
        Returns formatted activity items for display.
        """
        result = self.db.execute(
            select(AuditLog).order_by(AuditLog.changed_at.desc()).limit(limit)
        )
        logs = result.scalars().all()

        activities = []
        for log in logs:
            activities.append(
                {
                    "id": log.id,
                    "action": log.action,
                    "entity_type": log.table_name,
                    "entity_id": log.record_id,
                    "user_id": log.changed_by,
                    "timestamp": log.changed_at,
                    "description": self._format_activity(log),
                    "badge": self._get_activity_badge(log.action),
                }
            )

        return activities

    def _format_activity(self, log: AuditLog) -> str:
        """Format audit log entry for display."""
        action_map = {
            "CREATE": "created",
            "UPDATE": "updated",
            "DELETE": "deleted",
            "READ": "viewed",
            "BULK_READ": "listed",
        }
        action = action_map.get(log.action, log.action.lower())
        entity = log.table_name.replace("_", " ").title()
        return f"{entity} #{log.record_id} was {action}"

    def _get_activity_badge(self, action: str) -> Dict[str, str]:
        """Get badge styling for activity type."""
        badges = {
            "CREATE": {"text": "NEW", "class": "badge-primary"},
            "UPDATE": {"text": "UPD", "class": "badge-warning"},
            "DELETE": {"text": "DEL", "class": "badge-error"},
            "READ": {"text": "VIEW", "class": "badge-info"},
            "BULK_READ": {"text": "LIST", "class": "badge-ghost"},
        }
        return badges.get(action, {"text": action[:3], "class": "badge-ghost"})


# Convenience function
async def get_dashboard_service(db: Session) -> DashboardService:
    """Factory function for dependency injection."""
    return DashboardService(db)
