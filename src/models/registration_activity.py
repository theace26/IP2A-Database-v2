"""
RegistrationActivity model for referral audit trail.

Created: February 4, 2026 (Week 21 Session C)
Phase 7 - Referral & Dispatch System

Append-only event log for registration state changes.
Supplements the global audit_logs table (NLRA 7-year compliance).
"""
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.db.base import Base
from src.db.enums import RegistrationStatus, RegistrationAction

if TYPE_CHECKING:
    from src.models.member import Member
    from src.models.referral_book import ReferralBook
    from src.models.book_registration import BookRegistration
    from src.models.user import User


class RegistrationActivity(Base):
    """
    Audit trail for registration changes.

    This is an APPEND-ONLY table - no updates allowed.
    No updated_at column by design.

    Works alongside the global audit_logs table (ADR-012):
    - RegistrationActivity: domain-specific queries, reports
    - audit_logs: NLRA 7-year compliance, immutable PostgreSQL trigger

    Per Decision 5 in PHASE7_SCHEMA_DECISIONS.md, both are written
    for every registration state change.
    """

    __tablename__ = "registration_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Links
    registration_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("book_registrations.id"),
        nullable=True,
        index=True,
        comment="FK to registration (nullable for pre-registration actions)",
    )
    member_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("members.id"),
        nullable=False,
        index=True,
        comment="FK to member",
    )
    book_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("referral_books.id"),
        nullable=True,
        index=True,
        comment="FK to book (nullable for cross-book actions)",
    )

    # Activity details
    action: Mapped[RegistrationAction] = mapped_column(
        SAEnum(RegistrationAction),
        nullable=False,
        comment="The action that occurred",
    )
    activity_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="When the action occurred",
    )

    # State tracking
    previous_status: Mapped[Optional[RegistrationStatus]] = mapped_column(
        SAEnum(RegistrationStatus),
        nullable=True,
        comment="Status before the action",
    )
    new_status: Mapped[RegistrationStatus] = mapped_column(
        SAEnum(RegistrationStatus),
        nullable=False,
        comment="Status after the action",
    )
    previous_position: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Queue position before action",
    )
    new_position: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Queue position after action",
    )

    # Related entities
    labor_request_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("labor_requests.id", use_alter=True),
        nullable=True,
        comment="FK to labor request if dispatch-related",
    )
    dispatch_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("dispatches.id", use_alter=True),
        nullable=True,
        comment="FK to dispatch if dispatch-related",
    )

    # Context
    details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable description of the action",
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Reason for the action (rolloff reason, exempt reason, etc.)",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes",
    )

    # Who performed the action
    performed_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="User who performed the action",
    )
    processor: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Display name: 'SYSTEM', 'MEMBER VIA WEB', staff name",
    )

    # Timestamp (append-only - no updated_at)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="When this record was created",
    )

    # Relationships
    registration: Mapped[Optional["BookRegistration"]] = relationship(
        "BookRegistration",
        back_populates="activities",
    )
    member: Mapped["Member"] = relationship("Member", lazy="joined")
    book: Mapped[Optional["ReferralBook"]] = relationship("ReferralBook")
    performed_by: Mapped["User"] = relationship("User", lazy="joined")

    def __repr__(self) -> str:
        return (
            f"<RegistrationActivity(id={self.id}, action={self.action.value}, "
            f"member_id={self.member_id})>"
        )
