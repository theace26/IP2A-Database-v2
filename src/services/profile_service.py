"""Service layer for user profile management."""
from typing import Optional
from sqlalchemy.orm import Session

from src.models.user import User
from src.core.security import hash_password, verify_password
from src.services.audit_service import log_update


class ProfileService:
    """Service for user profile operations."""

    def get_profile(self, db: Session, user_id: int) -> Optional[User]:
        """Get user profile by ID."""
        return db.query(User).filter(User.id == user_id).first()

    def update_profile(
        self,
        db: Session,
        user: User,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        """Update user profile information."""
        old_values = {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

        if email is not None:
            user.email = email
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name

        new_values = {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

        # Audit the update
        log_update(
            db=db,
            table_name="users",
            record_id=user.id,
            user_id=user.id,
            old_values=old_values,
            new_values=new_values,
        )

        db.commit()
        db.refresh(user)
        return user

    def change_password(
        self,
        db: Session,
        user: User,
        current_password: str,
        new_password: str,
    ) -> tuple[bool, str]:
        """
        Change user password.

        Returns:
            (success: bool, message: str)
        """
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            return False, "Current password is incorrect"

        # Validate new password
        if len(new_password) < 8:
            return False, "New password must be at least 8 characters"

        if new_password == current_password:
            return False, "New password must be different from current password"

        # Hash and save new password
        user.password_hash = hash_password(new_password)
        user.must_change_password = False  # Clear password change requirement

        # Audit the password change (don't log actual password)
        log_update(
            db=db,
            table_name="users",
            record_id=user.id,
            user_id=user.id,
            old_values={"password": "[CHANGED]"},
            new_values={"password": "[CHANGED]"},
            notes="Password changed by user",
        )

        db.commit()
        return True, "Password changed successfully"

    def get_user_activity_summary(self, db: Session, user_id: int) -> dict:
        """Get summary of user's recent activity."""
        from src.models.audit_log import AuditLog
        from sqlalchemy import func
        from datetime import datetime, timedelta

        week_ago = datetime.utcnow() - timedelta(days=7)

        # Count actions this week
        action_counts = db.query(
            AuditLog.action,
            func.count(AuditLog.id)
        ).filter(
            AuditLog.user_id == user_id,
            AuditLog.created_at >= week_ago
        ).group_by(AuditLog.action).all()

        total = sum(c for _, c in action_counts)

        return {
            "actions_this_week": dict(action_counts),
            "total_actions_this_week": total,
        }


# Singleton instance
profile_service = ProfileService()
