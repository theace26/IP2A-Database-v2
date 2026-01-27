"""Benevolence application model for financial assistance requests."""

from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, Numeric, Enum as SAEnum
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import BenevolenceReason, BenevolenceStatus


class BenevolenceApplication(Base, TimestampMixin, SoftDeleteMixin):
    """Financial assistance request from a union member."""

    __tablename__ = "benevolence_applications"

    id = Column(Integer, primary_key=True, index=True)

    # Applicant
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)

    # Application details
    application_date = Column(Date, nullable=False)
    reason = Column(SAEnum(BenevolenceReason), nullable=False)
    description = Column(Text, nullable=False)
    amount_requested = Column(Numeric(10, 2), nullable=False)

    # Outcome
    status = Column(
        SAEnum(BenevolenceStatus),
        default=BenevolenceStatus.DRAFT,
        nullable=False,
        index=True,
    )
    approved_amount = Column(Numeric(10, 2))
    payment_date = Column(Date)
    payment_method = Column(String(50))

    # Notes
    notes = Column(Text)

    # Relationships
    member = relationship("Member", backref="benevolence_applications")
    reviews = relationship("BenevolenceReview", back_populates="application")

    def __repr__(self):
        return f"<BenevolenceApplication(id={self.id}, member_id={self.member_id}, status='{self.status}')>"
