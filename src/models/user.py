"""User model for authentication."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from src.models.member import Member
    from src.models.role import Role
    from src.models.user_role import UserRole
    from src.models.refresh_token import RefreshToken
    from src.models.email_token import EmailToken


class User(Base, TimestampMixin, SoftDeleteMixin):
    """
    User account for authentication.

    A User may optionally be linked to a Member record.
    Users have roles assigned through the UserRole junction table.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile fields
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Security tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Optional link to Member
    member_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,  # One user per member
    )

    # Relationships
    member: Mapped[Optional["Member"]] = relationship(
        "Member", back_populates="user", lazy="joined"
    )

    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    email_tokens: Mapped[list["EmailToken"]] = relationship(
        "EmailToken",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def roles(self) -> list["Role"]:
        """Return list of roles assigned to this user."""
        return [ur.role for ur in self.user_roles if ur.role]

    @property
    def role_names(self) -> list[str]:
        """Return list of role names for this user."""
        return [ur.role.name for ur in self.user_roles if ur.role]

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return role_name.lower() in [r.lower() for r in self.role_names]

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
