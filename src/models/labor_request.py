"""
LaborRequest model for employer job requests.

Created: February 4, 2026 (Week 21 Session A)
Phase 7 - Referral & Dispatch System

Represents an employer's request for workers. Must be received
by 3:00 PM for next morning referral per Local 46 rules.
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
    LaborRequestStatus,
    BookClassification,
    BookRegion,
    NoCheckMarkReason,
    AgreementType,
    JobClass,
)

if TYPE_CHECKING:
    from src.models.organization import Organization
    from src.models.referral_book import ReferralBook
    from src.models.member import Member
    from src.models.user import User
    from src.models.job_bid import JobBid
    from src.models.dispatch import Dispatch


class LaborRequest(Base, TimestampMixin):
    """
    Employer request for workers.

    Per Local 46 Referral Procedures:
    - Requests must be received by 3:00 PM for next morning referral
    - Short calls are <=10 business days
    - Online bidding window: 5:30 PM to 7:00 AM
    """

    __tablename__ = "labor_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Employer (FK to existing Organization model)
    employer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
        comment="FK to employer organization",
    )
    employer_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Denormalized employer name for display",
    )

    # Book/Classification
    book_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("referral_books.id"),
        nullable=True,
        index=True,
        comment="FK to specific referral book",
    )
    contract_code: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
        comment="Contract code: WIREPERSON, SOUND_COMM, etc.",
    )
    job_class: Mapped[Optional[JobClass]] = mapped_column(
        SAEnum(JobClass),
        nullable=True,
        comment="Job classification for this request",
    )
    classification: Mapped[Optional[BookClassification]] = mapped_column(
        SAEnum(BookClassification),
        nullable=True,
        comment="Book classification type",
    )
    region: Mapped[Optional[BookRegion]] = mapped_column(
        SAEnum(BookRegion),
        nullable=True,
        comment="Geographic region for the request",
    )

    # Request info
    request_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        index=True,
        comment="Internal tracking number",
    )
    request_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="When request was submitted",
    )

    # Position details
    workers_requested: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Number of workers requested",
    )
    workers_dispatched: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of workers already dispatched",
    )
    wage_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Hourly wage rate",
    )

    # Worksite
    worksite_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Job site name",
    )
    worksite_address: Mapped[Optional[str]] = mapped_column(
        String(300),
        nullable=True,
        comment="Job site street address",
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="City",
    )
    state: Mapped[str] = mapped_column(
        String(2),
        default="WA",
        nullable=False,
        comment="State (default WA)",
    )
    report_to_address: Mapped[Optional[str]] = mapped_column(
        String(300),
        nullable=True,
        comment="Where to report (may differ from worksite)",
    )

    # Schedule
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="When the job starts",
    )
    start_time: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
        comment="Job start time",
    )
    estimated_duration_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Estimated job duration in business days",
    )

    # Request type flags
    is_short_call: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Short call (<=10 business days)",
    )
    short_call_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="If short call, number of days",
    )
    is_foreperson_by_name: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Foreperson requested by name",
    )
    foreperson_member_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("members.id"),
        nullable=True,
        comment="FK to requested foreperson",
    )

    # Check mark rules
    generates_check_mark: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this request generates check marks",
    )
    no_check_mark_reason: Mapped[Optional[NoCheckMarkReason]] = mapped_column(
        SAEnum(NoCheckMarkReason),
        nullable=True,
        comment="Why no check marks (if applicable)",
    )

    # Special agreements
    agreement_type: Mapped[Optional[AgreementType]] = mapped_column(
        SAEnum(AgreementType),
        nullable=True,
        comment="PLA/CWA/TERO agreement type",
    )

    # Requirements and comments
    requirements: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Job requirements (certifications, drug test, etc.)",
    )
    comments: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional comments/instructions",
    )

    # Status
    status: Mapped[LaborRequestStatus] = mapped_column(
        SAEnum(LaborRequestStatus),
        default=LaborRequestStatus.OPEN,
        nullable=False,
        comment="Current request status",
    )

    # Online bidding
    allows_online_bidding: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether online bidding is enabled",
    )
    bidding_opens_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When bidding opens (5:30 PM day before)",
    )
    bidding_closes_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When bidding closes (7:00 AM day of)",
    )

    # Created by
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="User who created this request",
    )

    # Relationships
    employer: Mapped["Organization"] = relationship("Organization", lazy="joined")
    book: Mapped[Optional["ReferralBook"]] = relationship("ReferralBook")
    foreperson: Mapped[Optional["Member"]] = relationship("Member", lazy="joined")
    created_by: Mapped[Optional["User"]] = relationship("User", lazy="joined")
    bids: Mapped[list["JobBid"]] = relationship(
        "JobBid",
        back_populates="labor_request",
        cascade="all, delete-orphan",
    )
    dispatches: Mapped[list["Dispatch"]] = relationship(
        "Dispatch",
        back_populates="labor_request",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<LaborRequest(id={self.id}, employer={self.employer_name}, "
            f"workers={self.workers_requested}, status={self.status.value})>"
        )

    @property
    def is_filled(self) -> bool:
        """Whether all requested workers have been dispatched."""
        return self.workers_dispatched >= self.workers_requested

    @property
    def workers_remaining(self) -> int:
        """Number of workers still needed."""
        return max(0, self.workers_requested - self.workers_dispatched)

    @property
    def is_bidding_open(self) -> bool:
        """Whether online bidding is currently open."""
        if not self.allows_online_bidding:
            return False
        now = datetime.utcnow()
        if self.bidding_opens_at and self.bidding_closes_at:
            return self.bidding_opens_at <= now <= self.bidding_closes_at
        return False
