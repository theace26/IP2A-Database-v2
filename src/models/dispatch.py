"""
Dispatch model for job assignments.

Created: February 4, 2026 (Week 21 Session B)
Phase 7 - Referral & Dispatch System

Central transaction record linking a member to an employer via
a labor request. Creates corresponding MemberEmployment record.
"""
from typing import TYPE_CHECKING, Optional
from datetime import datetime, date, time
from decimal import Decimal

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    Time,
    DateTime,
    Numeric,
    ForeignKey,
    Text,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.db.base import Base
from src.db.mixins import TimestampMixin
from src.db.enums import (
    DispatchStatus,
    DispatchMethod,
    DispatchType,
    TermReason,
    JobClass,
)

if TYPE_CHECKING:
    from src.models.labor_request import LaborRequest
    from src.models.member import Member
    from src.models.book_registration import BookRegistration
    from src.models.job_bid import JobBid
    from src.models.organization import Organization
    from src.models.member_employment import MemberEmployment
    from src.models.user import User


class Dispatch(Base, TimestampMixin):
    """
    Job assignment from labor request to member.

    Per Local 46 Referral Procedures:
    - Creates corresponding MemberEmployment record
    - Must check in with employer by 3:00 PM on dispatch day
    - Quit/discharge = rolled off ALL books
    - Short calls <=10 days, position restored (max 2x)

    All dispatch actions generate audit trail entries (ADR-012).
    """

    __tablename__ = "dispatches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Core relationships
    labor_request_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("labor_requests.id"),
        nullable=False,
        index=True,
        comment="FK to labor request",
    )
    member_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("members.id"),
        nullable=False,
        index=True,
        comment="FK to dispatched member",
    )
    registration_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("book_registrations.id"),
        nullable=True,
        index=True,
        comment="FK to book registration at time of dispatch",
    )
    bid_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("job_bids.id"),
        nullable=True,
        comment="FK to bid if dispatched via online bidding",
    )
    employer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
        comment="FK to employer organization",
    )

    # Dispatch details
    dispatch_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="When dispatch was made",
    )
    dispatch_method: Mapped[DispatchMethod] = mapped_column(
        SAEnum(DispatchMethod),
        default=DispatchMethod.MORNING_REFERRAL,
        nullable=False,
        comment="How dispatch was made",
    )
    dispatch_type: Mapped[DispatchType] = mapped_column(
        SAEnum(DispatchType),
        default=DispatchType.NORMAL,
        nullable=False,
        comment="Type of dispatch (normal, short_call, emergency)",
    )
    dispatched_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="User who made the dispatch",
    )

    # Job classification (denormalized from request)
    job_class: Mapped[Optional[JobClass]] = mapped_column(
        SAEnum(JobClass),
        nullable=True,
        comment="Job classification",
    )
    book_code: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
        comment="Referral book code at time of dispatch",
    )
    contract_code: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
        comment="Contract code",
    )

    # Worksite (denormalized)
    worksite: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Worksite name",
    )
    worksite_code: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
        comment="Worksite code",
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="City",
    )

    # Schedule
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Job start date",
    )
    start_time: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
        comment="Job start time",
    )
    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Expected job end date",
    )

    # Rates
    start_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Hourly rate at start",
    )
    term_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Hourly rate at termination",
    )

    # Status
    dispatch_status: Mapped[DispatchStatus] = mapped_column(
        SAEnum(DispatchStatus),
        default=DispatchStatus.DISPATCHED,
        nullable=False,
        comment="Current dispatch status",
    )

    # Check-in tracking (by 3:00 PM per rules)
    check_in_deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Deadline to check in with employer (3:00 PM)",
    )
    checked_in: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether member checked in",
    )
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When member checked in",
    )

    # Short call tracking
    is_short_call: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is a short call (<=10 days)",
    )
    restore_to_book: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether to restore position after short call",
    )
    restored_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When position was restored",
    )

    # Termination tracking
    term_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Actual termination date",
    )
    term_reason: Mapped[Optional[TermReason]] = mapped_column(
        SAEnum(TermReason),
        nullable=True,
        comment="Termination reason",
    )
    term_comment: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Additional termination details",
    )
    days_worked: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total days worked",
    )
    hours_worked: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Total hours worked",
    )

    # Foreperson restriction (can't fill by-name for 2 weeks after quit)
    foreperson_restriction_until: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date until foreperson by-name restriction expires",
    )

    # Link to employment record
    employment_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("member_employments.id"),
        nullable=True,
        comment="FK to created MemberEmployment record",
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes",
    )

    # Relationships
    labor_request: Mapped["LaborRequest"] = relationship(
        "LaborRequest", back_populates="dispatches"
    )
    member: Mapped["Member"] = relationship("Member", lazy="joined")
    registration: Mapped[Optional["BookRegistration"]] = relationship(
        "BookRegistration"
    )
    bid: Mapped[Optional["JobBid"]] = relationship("JobBid")
    employer: Mapped["Organization"] = relationship("Organization", lazy="joined")
    employment: Mapped[Optional["MemberEmployment"]] = relationship(
        "MemberEmployment"
    )
    dispatched_by: Mapped["User"] = relationship("User", lazy="joined")

    def __repr__(self) -> str:
        return (
            f"<Dispatch(id={self.id}, member_id={self.member_id}, "
            f"employer_id={self.employer_id}, status={self.dispatch_status.value})>"
        )

    @property
    def is_active(self) -> bool:
        """Whether dispatch is currently active (working)."""
        return self.dispatch_status in (
            DispatchStatus.DISPATCHED,
            DispatchStatus.CHECKED_IN,
            DispatchStatus.WORKING,
        )

    @property
    def is_completed(self) -> bool:
        """Whether dispatch is completed or terminated."""
        return self.dispatch_status in (
            DispatchStatus.COMPLETED,
            DispatchStatus.TERMINATED,
        )

    @property
    def was_quit_or_fired(self) -> bool:
        """Whether member quit or was fired (triggers ALL-book rolloff)."""
        return self.term_reason in (TermReason.QUIT, TermReason.FIRED)

    @property
    def should_restore_position(self) -> bool:
        """Whether position should be restored (short call ended normally)."""
        return (
            self.is_short_call
            and self.restore_to_book
            and self.term_reason == TermReason.SHORT_CALL_END
        )
