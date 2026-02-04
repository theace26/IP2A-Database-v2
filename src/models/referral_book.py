"""
ReferralBook model for out-of-work lists.

Created: February 4, 2026 (Week 20 Session B)
Phase 7 - Referral & Dispatch System

Each book represents a specific classification + region combination.
Per Local 46 rules, regions (Seattle, Bremerton, Port Angeles) have
separate check mark tracking.
"""
from typing import TYPE_CHECKING, Optional
from datetime import time

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Time,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.db.base import Base
from src.db.mixins import TimestampMixin
from src.db.enums import BookClassification, BookRegion

if TYPE_CHECKING:
    from src.models.book_registration import BookRegistration


class ReferralBook(Base, TimestampMixin):
    """
    Out-of-work list definition.

    Each book represents a combination of:
    - Classification (inside_wireperson, tradeshow, sound_comm, etc.)
    - Region (seattle, bremerton, port_angeles)
    - Book number (1 = local members, 2 = travelers)

    Per Local 46 Referral Procedures:
    - Morning referral schedule varies by classification
    - 30-day re-sign requirement
    - 2 check marks allowed, 3rd = rolled off
    - Check marks are region-specific (Seattle requests don't affect Bremerton books)
    """

    __tablename__ = "referral_books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Identification
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Display name: 'Wire Seattle'"
    )
    code: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique code: 'WIRE_SEA_1'",
    )

    # Classification
    classification: Mapped[BookClassification] = mapped_column(
        SAEnum(BookClassification),
        nullable=False,
        comment="Job classification type",
    )
    book_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Book tier: 1=local members, 2=travelers, 3=other",
    )

    # Region (CRITICAL - separate check mark tracking per region)
    region: Mapped[BookRegion] = mapped_column(
        SAEnum(BookRegion),
        nullable=False,
        comment="Geographic region - check marks are region-specific",
    )

    # Referral Schedule
    referral_start_time: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
        comment="Morning referral time (e.g., 08:30 for Inside Wire)",
    )

    # Rules (from Local 46 Referral Procedures)
    re_sign_days: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
        comment="Days before re-sign required (default 30)",
    )
    max_check_marks: Mapped[int] = mapped_column(
        Integer,
        default=2,
        nullable=False,
        comment="Check marks allowed before rolloff (3rd = rolled off)",
    )
    grace_period_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Grace period days after re-sign deadline",
    )
    max_days_on_book: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Max days before auto-rolloff (null = no limit)",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this book is currently accepting registrations",
    )
    internet_bidding_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether online bidding is allowed for this book",
    )

    # Relationships
    registrations: Mapped[list["BookRegistration"]] = relationship(
        "BookRegistration",
        back_populates="book",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ReferralBook(id={self.id}, code='{self.code}', name='{self.name}')>"

    @property
    def full_name(self) -> str:
        """Full display name with book number."""
        return f"{self.name} Book {self.book_number}"

    @property
    def is_wire_book(self) -> bool:
        """Whether this is an Inside Wireperson book."""
        return self.classification == BookClassification.INSIDE_WIREPERSON
