"""Analytics service for aggregated metrics and trends."""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session

from src.models import Member, Student, AuditLog
from src.models.dues_payment import DuesPayment
from src.models.dues_period import DuesPeriod
from src.db.enums import MemberStatus, DuesPaymentStatus, StudentStatus


class AnalyticsService:
    """Service for analytics and metrics calculations."""

    def __init__(self, db: Session):
        self.db = db

    def get_membership_stats(self) -> dict:
        """Get current membership statistics."""
        total = self.db.scalar(select(func.count(Member.id))) or 0
        active = self.db.scalar(
            select(func.count(Member.id)).where(Member.status == MemberStatus.ACTIVE)
        ) or 0

        # New members this month
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_this_month = self.db.scalar(
            select(func.count(Member.id)).where(Member.created_at >= month_start)
        ) or 0

        # Retention rate (active / total who were ever active)
        retention_rate = (active / total * 100) if total > 0 else 0

        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "new_this_month": new_this_month,
            "retention_rate": round(retention_rate, 1),
        }

    def get_membership_trend(self, months: int = 12) -> list[dict]:
        """Get membership count by month for trending."""
        results = []
        now = datetime.utcnow()

        for i in range(months - 1, -1, -1):
            # Calculate month boundaries
            month_date = now - timedelta(days=30 * i)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            if month_date.month == 12:
                month_end = month_date.replace(year=month_date.year + 1, month=1, day=1)
            else:
                month_end = month_date.replace(month=month_date.month + 1, day=1)

            # Count members active at end of month
            count = self.db.scalar(
                select(func.count(Member.id))
                .where(Member.created_at < month_end)
                .where(
                    or_(
                        Member.status == MemberStatus.ACTIVE,
                        Member.updated_at >= month_start,
                    )
                )
            ) or 0

            results.append(
                {
                    "month": month_start.strftime("%Y-%m"),
                    "label": month_start.strftime("%b %Y"),
                    "count": count,
                }
            )

        return results

    def get_dues_analytics(self, period_id: Optional[int] = None) -> dict:
        """Get dues collection analytics."""
        # Build base filter
        paid_statuses = [DuesPaymentStatus.PAID, DuesPaymentStatus.PARTIAL]

        # Total collected
        stmt = select(func.sum(DuesPayment.amount_paid)).where(
            DuesPayment.status.in_(paid_statuses)
        )
        if period_id:
            stmt = stmt.where(DuesPayment.period_id == period_id)
        total_collected = self.db.scalar(stmt) or 0

        # Payment count
        stmt = select(func.count(DuesPayment.id)).where(
            DuesPayment.status.in_(paid_statuses)
        )
        if period_id:
            stmt = stmt.where(DuesPayment.period_id == period_id)
        payment_count = self.db.scalar(stmt) or 0

        # Average payment
        avg_payment = float(total_collected) / payment_count if payment_count > 0 else 0

        # Payment method breakdown
        stmt = (
            select(
                DuesPayment.payment_method,
                func.count(DuesPayment.id).label("count"),
                func.sum(DuesPayment.amount_paid).label("total"),
            )
            .where(DuesPayment.status.in_(paid_statuses))
            .where(DuesPayment.payment_method.isnot(None))
            .group_by(DuesPayment.payment_method)
        )
        if period_id:
            stmt = stmt.where(DuesPayment.period_id == period_id)

        method_results = self.db.execute(stmt).fetchall()

        methods = [
            {
                "method": str(row.payment_method.value) if row.payment_method else "Unknown",
                "count": row.count,
                "total": float(row.total or 0),
            }
            for row in method_results
        ]

        return {
            "total_collected": float(total_collected),
            "payment_count": payment_count,
            "average_payment": round(avg_payment, 2),
            "payment_methods": methods,
        }

    def get_delinquency_report(self) -> dict:
        """Get members with overdue dues."""
        now = datetime.utcnow()

        # Find current period
        current_period = self.db.scalar(
            select(DuesPeriod)
            .where(DuesPeriod.period_year == now.year)
            .where(DuesPeriod.period_month == now.month)
        )

        if not current_period:
            return {"overdue_count": 0, "overdue_amount": 0, "period": None, "members": []}

        # Members with overdue status for current period
        overdue_payments = self.db.execute(
            select(DuesPayment)
            .where(DuesPayment.period_id == current_period.id)
            .where(DuesPayment.status == DuesPaymentStatus.OVERDUE)
            .limit(100)
        ).scalars().all()

        # Get member details
        members_list = []
        for payment in overdue_payments[:20]:
            if payment.member:
                members_list.append(
                    {
                        "id": payment.member.id,
                        "name": f"{payment.member.first_name} {payment.member.last_name}",
                        "member_number": payment.member.member_number,
                        "amount_due": float(payment.balance_due),
                    }
                )

        total_overdue = sum(float(p.balance_due) for p in overdue_payments)

        return {
            "overdue_count": len(overdue_payments),
            "overdue_amount": round(total_overdue, 2),
            "period": current_period.period_name,
            "members": members_list,
        }

    def get_training_metrics(self) -> dict:
        """Get training program effectiveness metrics."""
        total_students = self.db.scalar(select(func.count(Student.id))) or 0

        # ENROLLED is the active status for students
        active_students = self.db.scalar(
            select(func.count(Student.id)).where(Student.status == StudentStatus.ENROLLED)
        ) or 0

        completed = self.db.scalar(
            select(func.count(Student.id)).where(Student.status == StudentStatus.COMPLETED)
        ) or 0

        # DROPPED is the withdrawal status for students
        withdrawn = self.db.scalar(
            select(func.count(Student.id)).where(Student.status == StudentStatus.DROPPED)
        ) or 0

        completion_rate = (completed / total_students * 100) if total_students > 0 else 0

        return {
            "total_students": total_students,
            "active": active_students,
            "completed": completed,
            "withdrawn": withdrawn,
            "completion_rate": round(completion_rate, 1),
        }

    def get_activity_metrics(self, days: int = 30) -> dict:
        """Get system activity metrics."""
        since = datetime.utcnow() - timedelta(days=days)

        # Audit log counts by action
        action_counts = self.db.execute(
            select(AuditLog.action, func.count(AuditLog.id).label("count"))
            .where(AuditLog.changed_at >= since)
            .group_by(AuditLog.action)
        ).fetchall()

        actions = {str(row.action): row.count for row in action_counts}

        # Daily activity for chart
        daily_activity = self.db.execute(
            select(
                func.date(AuditLog.changed_at).label("date"),
                func.count(AuditLog.id).label("count"),
            )
            .where(AuditLog.changed_at >= since)
            .group_by(func.date(AuditLog.changed_at))
            .order_by(func.date(AuditLog.changed_at))
        ).fetchall()

        daily = [{"date": str(row.date), "count": row.count} for row in daily_activity]

        return {
            "period_days": days,
            "action_breakdown": actions,
            "total_actions": sum(actions.values()),
            "daily_activity": daily,
        }
