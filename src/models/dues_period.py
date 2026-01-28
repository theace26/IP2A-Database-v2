"""DuesPeriod model for monthly billing periods."""

import calendar
from sqlalchemy import Column, Integer, Date, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin


class DuesPeriod(Base, TimestampMixin):
    """Monthly dues billing period."""

    __tablename__ = "dues_periods"

    id = Column(Integer, primary_key=True, index=True)
    period_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=False)  # 1-12
    due_date = Column(Date, nullable=False)  # When dues are due
    grace_period_end = Column(Date, nullable=False)  # End of grace period
    is_closed = Column(Boolean, default=False)  # Period closed for new charges
    closed_at = Column(DateTime, nullable=True)
    closed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    closed_by = relationship("User", foreign_keys=[closed_by_id])
    payments = relationship("DuesPayment", back_populates="period")

    __table_args__ = (
        UniqueConstraint('period_year', 'period_month', name='uq_dues_period_year_month'),
    )

    @property
    def period_name(self) -> str:
        """Return formatted period name like 'January 2026'."""
        return f"{calendar.month_name[self.period_month]} {self.period_year}"

    def __repr__(self):
        return f"<DuesPeriod(id={self.id}, period='{self.period_name}')>"
