"""Member model for union members."""

from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, Date, Text, Enum as SAEnum
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import MemberStatus, MemberClassification

if TYPE_CHECKING:
    pass


class Member(Base, TimestampMixin, SoftDeleteMixin):
    """Union member entity."""

    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)

    # Member identification (alphanumeric: 7464416, a22555555, d5555555)
    member_number = Column(String(50), unique=True, nullable=False, index=True)

    # Personal info
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))

    # Contact
    address = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    phone = Column(String(50))
    email = Column(String(255))

    # Dates
    date_of_birth = Column(Date)
    hire_date = Column(Date)  # When they joined the union

    # Classification & Status
    status = Column(SAEnum(MemberStatus), default=MemberStatus.ACTIVE, nullable=False)
    classification = Column(SAEnum(MemberClassification), nullable=False)

    # General notes (deprecated - use MemberNote relationship for staff notes)
    general_notes = Column("notes", Text)

    # Stripe Integration
    stripe_customer_id = Column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
        comment="Stripe customer ID for payment processing"
    )

    # Relationships
    student = relationship("Student", back_populates="member", uselist=False)
    employments = relationship("MemberEmployment", back_populates="member")
    user = relationship("User", back_populates="member", uselist=False)
    dues_payments = relationship("DuesPayment", back_populates="member")
    dues_adjustments = relationship("DuesAdjustment", back_populates="member")
    notes = relationship(
        "MemberNote",
        back_populates="member",
        cascade="all, delete-orphan",
        order_by="desc(MemberNote.created_at)"
    )

    # Phase 7 - Referral & Dispatch relationships
    book_registrations = relationship(
        "BookRegistration",
        back_populates="member",
        cascade="all, delete-orphan",
        order_by="desc(BookRegistration.registration_date)"
    )

    def __repr__(self):
        return f"<Member(id={self.id}, number='{self.member_number}', name='{self.first_name} {self.last_name}')>"
