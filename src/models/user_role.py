"""UserRole junction model for many-to-many user-role relationship."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, ForeignKey, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.role import Role


class UserRole(Base, TimestampMixin):
    """
    Junction table linking Users to Roles.

    Uses Association Object pattern to allow additional metadata
    on the user-role relationship (e.g., who assigned it, when it expires).
    """

    __tablename__ = "user_roles"

    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Metadata about the role assignment
    assigned_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
