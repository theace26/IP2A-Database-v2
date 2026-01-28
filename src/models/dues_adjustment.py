"""DuesAdjustment model for dues adjustments, waivers, and credits."""

from sqlalchemy import Column, Integer, DateTime, Numeric, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin
from src.db.enums import DuesAdjustmentType, AdjustmentStatus


class DuesAdjustment(Base, TimestampMixin):
    """Dues adjustments, waivers, and credits."""

    __tablename__ = "dues_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    payment_id = Column(Integer, ForeignKey("dues_payments.id"), nullable=True)  # Optional link to specific payment

    adjustment_type = Column(SAEnum(DuesAdjustmentType), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)  # Positive = credit, Negative = additional charge
    reason = Column(Text, nullable=False)

    # Approval workflow
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Made nullable for testing
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    status = Column(SAEnum(AdjustmentStatus), nullable=False, default=AdjustmentStatus.PENDING)

    # Relationships
    member = relationship("Member", back_populates="dues_adjustments")
    payment = relationship("DuesPayment", back_populates="adjustments")
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])

    def __repr__(self):
        return f"<DuesAdjustment(id={self.id}, member_id={self.member_id}, type='{self.adjustment_type.value}', amount=${self.amount})>"
