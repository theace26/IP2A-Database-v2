"""
JobBid model for member bids on labor requests.

Created: February 4, 2026 (Week 21 Session A)
Phase 7 - Referral & Dispatch System

Tracks member bids on labor requests (online/email bidding).
Per Local 46: Online bidding 5:30 PM - 7:00 AM.
"""
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.db.base import Base
from src.db.mixins import TimestampMixin
from src.db.enums import BidStatus

if TYPE_CHECKING:
    from src.models.labor_request import LaborRequest
    from src.models.member import Member
    from src.models.book_registration import BookRegistration
    from src.models.dispatch import Dispatch


class JobBid(Base, TimestampMixin):
    """
    Member bid on a labor request.

    Per Local 46 Referral Procedures:
    - Online/email bidding: 5:30 PM to 7:00 AM
    - Must check in with employer by 3:00 PM on dispatch day
    - Reject after bidding = considered a quit
    - 2nd rejection in 12 months = lose internet privileges for 1 year

    This separate model (vs. embedding in Dispatch) provides:
    - Complete bid history for reports (B-18, AP-08, C-42, C-43, C-44)
    - Tracking of bids that didn't result in dispatch
    - Proper audit trail for rejection tracking
    """

    __tablename__ = "job_bids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Links
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
        comment="FK to member who bid",
    )
    registration_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("book_registrations.id"),
        nullable=True,
        index=True,
        comment="FK to member's registration on the book",
    )

    # Bid details
    bid_submitted_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="When the bid was submitted",
    )
    bid_method: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="How bid was submitted: online, email, in_person",
    )
    queue_position_at_bid: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Member's queue position when they bid",
    )

    # Status
    bid_status: Mapped[BidStatus] = mapped_column(
        SAEnum(BidStatus),
        default=BidStatus.PENDING,
        nullable=False,
        comment="Current bid status",
    )

    # Processing
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When bid was processed",
    )
    processed_by_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="User who processed the bid",
    )

    # Outcome
    was_dispatched: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this bid resulted in a dispatch",
    )
    dispatch_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("dispatches.id", use_alter=True),
        nullable=True,
        comment="FK to resulting dispatch (if any)",
    )

    # Rejection tracking (important for 1-year suspension rule)
    rejected_by_member: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether member rejected after accepting",
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Why bid was rejected",
    )
    rejection_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When rejection occurred",
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes",
    )

    # Relationships
    labor_request: Mapped["LaborRequest"] = relationship(
        "LaborRequest", back_populates="bids"
    )
    member: Mapped["Member"] = relationship("Member", lazy="joined")
    registration: Mapped[Optional["BookRegistration"]] = relationship(
        "BookRegistration"
    )
    dispatch: Mapped[Optional["Dispatch"]] = relationship(
        "Dispatch", foreign_keys="[Dispatch.bid_id]", back_populates="bid", uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<JobBid(id={self.id}, request_id={self.labor_request_id}, "
            f"member_id={self.member_id}, status={self.bid_status.value})>"
        )

    @property
    def is_pending(self) -> bool:
        """Whether bid is still pending."""
        return self.bid_status == BidStatus.PENDING

    @property
    def was_accepted(self) -> bool:
        """Whether bid was accepted."""
        return self.bid_status == BidStatus.ACCEPTED

    @property
    def counts_as_quit(self) -> bool:
        """Whether this rejection counts as a quit (per Local 46 rules)."""
        return self.rejected_by_member and self.bid_status == BidStatus.ACCEPTED
