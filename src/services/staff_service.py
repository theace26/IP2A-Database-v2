"""
Staff Service - User management operations.
Handles search, filtering, pagination, and CRUD for users.
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from datetime import datetime
import logging

from src.models.user import User
from src.models.role import Role
from src.models.user_role import UserRole

logger = logging.getLogger(__name__)


class StaffService:
    """Service for staff/user management operations."""

    def __init__(self, db: Session):
        self.db = db

    def search_users(
        self,
        query: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = "email",
        sort_order: str = "asc",
    ) -> Tuple[List[User], int, int]:
        """
        Search and filter users with pagination.

        Args:
            query: Search term (matches email, first_name, last_name)
            role: Filter by role name
            status: Filter by status ('active', 'locked', 'inactive', 'all')
            page: Page number (1-indexed)
            per_page: Results per page
            sort_by: Column to sort by
            sort_order: 'asc' or 'desc'

        Returns:
            Tuple of (users, total_count, total_pages)
        """
        # Base query with eager loading of roles through user_roles
        stmt = select(User).options(selectinload(User.user_roles).selectinload(UserRole.role))

        # Apply search filter
        if query and query.strip():
            search_term = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                )
            )

        # Apply role filter
        if role and role != "all":
            stmt = stmt.join(User.user_roles).join(UserRole.role).where(Role.name == role)

        # Apply status filter
        # Note: User model uses locked_until (datetime) instead of is_locked (bool)
        now = datetime.utcnow()
        if status == "active":
            stmt = stmt.where(
                and_(
                    User.is_active == True,
                    or_(User.locked_until == None, User.locked_until < now)
                )
            )
        elif status == "locked":
            stmt = stmt.where(
                and_(User.locked_until != None, User.locked_until >= now)
            )
        elif status == "inactive":
            stmt = stmt.where(User.is_active == False)
        # 'all' or None = no filter

        # Get total count (before pagination)
        count_stmt = select(func.count(func.distinct(User.id))).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar() or 0

        # Apply sorting
        sort_column = getattr(User, sort_by, User.email)
        if sort_order == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)

        # Execute query
        result = self.db.execute(stmt)
        users = result.unique().scalars().all()

        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1

        return list(users), total, total_pages

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a single user by ID with roles loaded."""
        stmt = (
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.id == user_id)
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_all_roles(self) -> List[Role]:
        """Get all available roles for filter dropdown."""
        stmt = select(Role).order_by(Role.name)
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def get_user_counts(self) -> dict:
        """Get counts for status badges."""
        now = datetime.utcnow()

        # Total users
        total = self.db.execute(select(func.count(User.id))).scalar() or 0

        # Active users (is_active=True and not currently locked)
        active = self.db.execute(
            select(func.count(User.id)).where(
                and_(
                    User.is_active == True,
                    or_(User.locked_until == None, User.locked_until < now)
                )
            )
        ).scalar() or 0

        # Locked users (locked_until is in the future)
        locked = self.db.execute(
            select(func.count(User.id)).where(
                and_(User.locked_until != None, User.locked_until >= now)
            )
        ).scalar() or 0

        # Inactive users (is_active=False)
        inactive = self.db.execute(
            select(func.count(User.id)).where(User.is_active == False)
        ).scalar() or 0

        return {
            "total": total,
            "active": active,
            "locked": locked,
            "inactive": inactive,
        }

    def is_user_locked(self, user: User) -> bool:
        """Check if a user is currently locked."""
        if user.locked_until is None:
            return False
        return user.locked_until >= datetime.utcnow()


def get_staff_service(db: Session) -> StaffService:
    """Factory function for dependency injection."""
    return StaffService(db)
