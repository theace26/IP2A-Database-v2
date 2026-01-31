"""DuesPayment model for individual dues payment records."""

from decimal import Decimal
from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import DuesPaymentMethod, DuesPaymentStatus


class DuesPayment(Base, TimestampMixin, SoftDeleteMixin):
    """Individual dues payment record."""

    __tablename__ = "dues_payments"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    period_id = Column(Integer, ForeignKey("dues_periods.id"), nullable=False, index=True)

    # Payment details
    amount_due = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), nullable=False, default=0)
    payment_date = Column(Date, nullable=True)
    payment_method = Column(SAEnum(DuesPaymentMethod), nullable=True)

    # Status
    status = Column(SAEnum(DuesPaymentStatus), nullable=False, default=DuesPaymentStatus.PENDING)

    # Reference info
    reference_number = Column(String(100), nullable=True)  # Check number, transaction ID
    receipt_number = Column(String(50), nullable=True, unique=True)

    # Processing
    processed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_at = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    member = relationship("Member", back_populates="dues_payments")
    period = relationship("DuesPeriod", back_populates="payments")
    processed_by = relationship("User", foreign_keys=[processed_by_id])
    adjustments = relationship("DuesAdjustment", back_populates="payment")

    @property
    def balance_due(self) -> Decimal:
        """Calculate remaining balance."""
        return Decimal(str(self.amount_due)) - Decimal(str(self.amount_paid))

    @property
    def is_paid_in_full(self) -> bool:
        """Check if payment is complete."""
        return Decimal(str(self.amount_paid)) >= Decimal(str(self.amount_due))

    def __repr__(self):
        return f"<DuesPayment(id={self.id}, member_id={self.member_id}, status='{self.status.value}')>"
