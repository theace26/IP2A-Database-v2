"""
BookRegistration model for member positions on out-of-work lists.

Created: February 4, 2026 (Week 20 Session C)
Phase 7 - Referral & Dispatch System

Tracks a member's position, status, and check marks on a referral book.
"""
from typing import TYPE_CHECKING, Optional
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    DateTime,
    Numeric,
    ForeignKey,
    Text,
    UniqueConstraint,
    Index,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.db.base import Base
from src.db.mixins import TimestampMixin
from src.db.enums import (
    RegistrationStatus,
    ExemptReason,
    RolloffReason,
)

if TYPE_CHECKING:
    from src.models.member import Member
    from src.models.referral_book import ReferralBook
    from src.models.registration_activity import RegistrationActivity


class BookRegistration(Base, TimestampMixin):
    """
    Member's position on an out-of-work list.

    Per Local 46 Referral Procedures:
    - Members register in person or via email
    - Must re-sign every 30 days
    - 2 check marks allowed, 3rd = rolled off
    - Exempt members skip check mark and re-sign requirements

    CRITICAL: registration_number (APN) is DECIMAL(10,2), NOT integer.
    The decimal portion preserves FIFO ordering from LaborPower.
    """

    __tablename__ = "book_registrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign keys
    member_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("members.id"),
        nullable=False,
        index=True,
        comment="FK to member",
    )
    book_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("referral_books.id"),
        nullable=False,
        index=True,
        comment="FK to referral book",
    )

    # Registration tracking
    registration_number: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        index=True,
        comment="APN - Applicant Priority Number (DECIMAL for FIFO ordering)",
    )
    registration_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="When member registered on book",
    )
    registration_method: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="How registered: in_person, email",
    )

    # Status
    status: Mapped[RegistrationStatus] = mapped_column(
        SAEnum(RegistrationStatus),
        default=RegistrationStatus.REGISTERED,
        nullable=False,
        comment="Current registration status",
    )

    # Re-sign tracking (every 30 days per rules)
    last_re_sign_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Last time member re-signed",
    )
    re_sign_deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Deadline for next re-sign (30 days from last)",
    )

    # Check marks (2 allowed, 3rd = rolloff)
    check_marks: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Current check mark count (3 = rolled off)",
    )
    consecutive_missed_check_marks: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Consecutive missed check marks (for auto-rolloff)",
    )
    has_check_mark: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether member currently has a check mark",
    )
    last_check_mark_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Last date a check mark was recorded (max 1 per day)",
    )
    last_check_mark_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Timestamp of last check mark",
    )
    no_check_mark_reason: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Reason check mark was not given",
    )
    check_mark_restored_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When check mark was restored by dispatcher",
    )

    # Short call tracking (max 2 restorations per rules)
    short_call_restorations: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Times registration restored after short call (max 2)",
    )

    # Exempt status (Decision 3: per-book exempt, not global)
    is_exempt: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether member is exempt on this book",
    )
    exempt_reason: Mapped[Optional[ExemptReason]] = mapped_column(
        SAEnum(ExemptReason),
        nullable=True,
        comment="Reason for exempt status",
    )
    exempt_start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="When exempt status was granted",
    )
    exempt_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="When exempt status expires (max 6 months per rules)",
    )

    # Rolloff tracking
    roll_off_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When member was rolled off",
    )
    roll_off_reason: Mapped[Optional[RolloffReason]] = mapped_column(
        SAEnum(RolloffReason),
        nullable=True,
        comment="Why member was rolled off",
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes about this registration",
    )

    # Relationships
    member: Mapped["Member"] = relationship("Member", lazy="joined")
    book: Mapped["ReferralBook"] = relationship(
        "ReferralBook", back_populates="registrations"
    )
    activities: Mapped[list["RegistrationActivity"]] = relationship(
        "RegistrationActivity",
        back_populates="registration",
        cascade="all, delete-orphan",
        order_by="desc(RegistrationActivity.created_at)",
    )

    # Constraints
    __table_args__ = (
        # A member can only have one active registration per book
        UniqueConstraint(
            "member_id",
            "book_id",
            "registration_number",
            name="uq_member_book_apn",
        ),
        # Index for queue ordering (lower APN = higher priority)
        Index("ix_book_queue_order", "book_id", "status", "registration_number"),
    )

    def __repr__(self) -> str:
        return (
            f"<BookRegistration(id={self.id}, member_id={self.member_id}, "
            f"book_id={self.book_id}, apn={self.registration_number})>"
        )

    @property
    def is_active(self) -> bool:
        """Whether registration is currently active on the book."""
        return self.status == RegistrationStatus.REGISTERED

    @property
    def is_rolled_off(self) -> bool:
        """Whether member has been rolled off."""
        return self.status == RegistrationStatus.ROLLED_OFF

    @property
    def can_be_dispatched(self) -> bool:
        """Whether member can be dispatched from this registration."""
        return self.status == RegistrationStatus.REGISTERED and not self.is_exempt

    @property
    def days_on_book(self) -> int:
        """Number of days since registration."""
        if self.registration_date:
            return (datetime.utcnow() - self.registration_date).days
        return 0

    @property
    def check_marks_remaining(self) -> int:
        """Number of check marks before rolloff."""
        return max(0, 2 - self.check_marks)
