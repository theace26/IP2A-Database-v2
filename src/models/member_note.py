"""Member notes model for staff documentation."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.models.member import Member
    from src.models.user import User


class NoteVisibility:
    """Visibility levels for member notes."""
    STAFF_ONLY = "staff_only"          # Only staff who created or admins
    OFFICERS = "officers"               # Officers and above
    ALL_AUTHORIZED = "all_authorized"   # Anyone with member view permission


class MemberNote(Base, TimestampMixin):
    """
    Staff notes about members.

    All changes to this table are automatically audited for NLRA compliance.
    Notes have visibility levels to control who can see sensitive information.
    """
    __tablename__ = "member_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign keys
    member_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Note content
    note_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Visibility control
    visibility: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=NoteVisibility.STAFF_ONLY,
        comment="Who can view this note: staff_only, officers, all_authorized"
    )

    # Categorization (optional)
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Optional category: contact, dues, grievance, general, etc."
    )

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    member: Mapped["Member"] = relationship("Member", back_populates="notes")
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])

    def __repr__(self) -> str:
        return f"<MemberNote(id={self.id}, member_id={self.member_id}, visibility={self.visibility})>"
