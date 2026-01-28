"""Service functions for UserRole model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from src.models.user_role import UserRole
from src.schemas.user_role import UserRoleCreate


def get_user_role(db: Session, user_id: int, role_id: int) -> Optional[UserRole]:
    """Get a specific user-role assignment."""
    stmt = select(UserRole).where(
        and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
    )
    return db.execute(stmt).scalar_one_or_none()


def get_user_roles(db: Session, user_id: int) -> list[UserRole]:
    """Get all roles for a user."""
    stmt = select(UserRole).where(UserRole.user_id == user_id)
    return list(db.execute(stmt).scalars().all())


def assign_role(db: Session, data: UserRoleCreate) -> UserRole:
    """Assign a role to a user."""
    user_role = UserRole(
        user_id=data.user_id,
        role_id=data.role_id,
        assigned_by=data.assigned_by,
        expires_at=data.expires_at,
    )
    db.add(user_role)
    db.commit()
    db.refresh(user_role)
    return user_role


def remove_role(db: Session, user_role: UserRole) -> None:
    """Remove a role from a user."""
    db.delete(user_role)
    db.commit()


def get_expired_roles(db: Session) -> list[UserRole]:
    """Get all expired role assignments."""
    stmt = select(UserRole).where(
        and_(UserRole.expires_at.isnot(None), UserRole.expires_at < datetime.utcnow())
    )
    return list(db.execute(stmt).scalars().all())
