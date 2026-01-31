"""Frontend service for audit log queries with role-based filtering."""
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func

from src.models.audit_log import AuditLog
from src.models.user import User
from src.core.permissions import (
    AuditPermission,
    has_audit_permission,
    redact_sensitive_fields,
    SENSITIVE_FIELDS
)


class AuditFrontendService:
    """Service for audit log frontend queries."""

    # Tables that contain member-related data
    MEMBER_TABLES = {
        "members", "member_notes", "member_employments",
        "dues_payments", "dues_adjustments",
        "grievances", "benevolence_applications",
        "salting_activities", "students",
    }

    # Tables that contain user/system data
    USER_TABLES = {
        "users", "user_sessions", "password_resets",
    }

    def _get_primary_role(self, user: User) -> str:
        """Get user's primary role (highest privilege role)."""
        role_priority = ["admin", "officer", "organizer", "staff", "instructor", "member"]
        user_roles = [r.lower() for r in user.role_names]

        for role in role_priority:
            if role in user_roles:
                return role

        return "member"  # Default fallback

    def get_audit_logs(
        self,
        db: Session,
        current_user: User,
        table_name: Optional[str] = None,
        record_id: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Dict[str, Any]:
        """
        Query audit logs with role-based filtering.

        Returns:
            {
                "items": [...],
                "total": int,
                "page": int,
                "per_page": int,
                "pages": int,
            }
        """
        query = db.query(AuditLog)

        # Apply role-based table filtering
        query = self._apply_role_filter(query, current_user)

        # Apply search filters
        if table_name:
            query = query.filter(AuditLog.table_name == table_name)

        if record_id:
            query = query.filter(AuditLog.record_id == str(record_id))

        if action:
            query = query.filter(AuditLog.action == action.upper())

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        if date_from:
            query = query.filter(AuditLog.created_at >= datetime.combine(date_from, datetime.min.time()))

        if date_to:
            query = query.filter(AuditLog.created_at <= datetime.combine(date_to, datetime.max.time()))

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    AuditLog.table_name.ilike(search_pattern),
                    AuditLog.changed_by.ilike(search_pattern),
                    AuditLog.notes.ilike(search_pattern),
                )
            )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(per_page).all()

        # Redact sensitive fields based on role
        primary_role = self._get_primary_role(current_user)
        items = [self._format_log(log, primary_role) for log in logs]

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }

    def _apply_role_filter(self, query, user: User):
        """Apply table filtering based on user's audit permissions."""
        primary_role = self._get_primary_role(user)

        # Admin with VIEW_ALL sees everything
        if has_audit_permission(primary_role, AuditPermission.VIEW_ALL):
            return query

        allowed_tables = set()

        # VIEW_MEMBERS permission grants access to member tables
        if has_audit_permission(primary_role, AuditPermission.VIEW_MEMBERS):
            allowed_tables.update(self.MEMBER_TABLES)

        # VIEW_USERS permission grants access to user tables
        if has_audit_permission(primary_role, AuditPermission.VIEW_USERS):
            allowed_tables.update(self.USER_TABLES)

        # VIEW_OWN grants access only to logs the user created
        if has_audit_permission(primary_role, AuditPermission.VIEW_OWN):
            if allowed_tables:
                # User can see their own logs OR logs from allowed tables
                return query.filter(
                    or_(
                        AuditLog.user_id == user.id,
                        AuditLog.table_name.in_(allowed_tables)
                    )
                )
            else:
                # User can only see their own logs
                return query.filter(AuditLog.user_id == user.id)

        # If user has no permissions but has allowed tables
        if allowed_tables:
            return query.filter(AuditLog.table_name.in_(allowed_tables))

        # No access - return empty result
        return query.filter(False)  # Always false = no results

    def _format_log(self, log: AuditLog, user_role: str) -> dict:
        """Format audit log with redaction for non-admin users."""
        return {
            "id": log.id,
            "table_name": log.table_name,
            "record_id": log.record_id,
            "action": log.action,
            "old_values": redact_sensitive_fields(log.old_values, user_role),
            "new_values": redact_sensitive_fields(log.new_values, user_role),
            "changed_fields": log.changed_fields,
            "changed_by": log.changed_by,
            "changed_at": log.created_at.isoformat() if log.created_at else None,
            "ip_address": log.ip_address if user_role == "admin" else None,
            "user_agent": None,  # Never expose user agent
            "notes": log.notes,
        }

    def get_entity_history(
        self,
        db: Session,
        current_user: User,
        table_name: str,
        record_id: str,
        limit: int = 20,
    ) -> List[dict]:
        """Get audit history for a specific entity."""
        query = db.query(AuditLog).filter(
            AuditLog.table_name == table_name,
            AuditLog.record_id == str(record_id),
        )

        # Apply role filter
        query = self._apply_role_filter(query, current_user)

        logs = query.order_by(desc(AuditLog.created_at)).limit(limit).all()

        primary_role = self._get_primary_role(current_user)
        return [self._format_log(log, primary_role) for log in logs]

    def get_available_tables(self, user: User) -> List[str]:
        """Get list of tables the user can view audits for."""
        primary_role = self._get_primary_role(user)

        if has_audit_permission(primary_role, AuditPermission.VIEW_ALL):
            return sorted(self.MEMBER_TABLES | self.USER_TABLES | {"audit_logs"})

        available = set()

        if has_audit_permission(primary_role, AuditPermission.VIEW_MEMBERS):
            available.update(self.MEMBER_TABLES)

        if has_audit_permission(primary_role, AuditPermission.VIEW_USERS):
            available.update(self.USER_TABLES)

        return sorted(available)

    def get_action_types(self) -> List[str]:
        """Get list of possible action types."""
        return ["CREATE", "READ", "UPDATE", "DELETE", "BULK_READ"]

    def get_stats(self, db: Session, current_user: User) -> dict:
        """Get audit statistics for dashboard."""
        query = db.query(AuditLog)
        query = self._apply_role_filter(query, current_user)

        today = date.today()
        week_ago = today - timedelta(days=7)

        # Count by action type (last 7 days)
        action_counts = db.query(
            AuditLog.action,
            func.count(AuditLog.id)
        ).filter(
            AuditLog.created_at >= datetime.combine(week_ago, datetime.min.time())
        ).group_by(AuditLog.action).all()

        return {
            "total_logs": query.count(),
            "logs_this_week": query.filter(
                AuditLog.created_at >= datetime.combine(week_ago, datetime.min.time())
            ).count(),
            "logs_today": query.filter(
                AuditLog.created_at >= datetime.combine(today, datetime.min.time())
            ).count(),
            "action_breakdown": {action: count for action, count in action_counts},
        }


# Singleton instance
audit_frontend_service = AuditFrontendService()
