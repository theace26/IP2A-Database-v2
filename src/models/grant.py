"""
Grant model for tracking funding sources and budgets.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Numeric,
    Boolean,
    Text,
    JSON,
    Index,
    Enum,
)

from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import GrantStatus


class Grant(TimestampMixin, SoftDeleteMixin, Base):
    """
    Tracks grants and funding sources for the IP2A program.

    Supports budget tracking, allowable expense categories,
    and links to actual expenses for reporting and compliance.
    """

    __tablename__ = "grants"

    id = Column(Integer, primary_key=True, index=True)

    # Grant identity
    name = Column(String(255), nullable=False, index=True)
    grant_number = Column(String(100), nullable=True, unique=True)  # Official grant ID
    funding_source = Column(
        String(255), nullable=True
    )  # e.g., "DOL", "State", "Private"

    # Budget tracking
    total_amount = Column(Numeric(12, 2), nullable=False)
    spent_amount = Column(Numeric(12, 2), nullable=True, default=0)

    # Grant period
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True, index=True)

    # Allowable expense categories (JSON array for flexibility)
    # Example: ["tools", "supplies", "travel", "instruction"]
    allowable_categories = Column(JSON, nullable=True)

    # Reporting requirements
    reporting_frequency = Column(
        String(50), nullable=True
    )  # monthly, quarterly, annual
    next_report_due = Column(Date, nullable=True)

    notes = Column(Text, nullable=True)

    # Grant status
    status = Column(
        Enum(GrantStatus, name="grant_status", create_constraint=True),
        nullable=False,
        default=GrantStatus.PENDING,
        index=True,
    )

    # Target metrics (for compliance tracking)
    target_enrollment = Column(Integer, nullable=True)  # Target number of students
    target_completion = Column(Integer, nullable=True)  # Target completions
    target_placement = Column(Integer, nullable=True)   # Target job placements

    # Status (note: is_deleted from mixin handles soft delete separately)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationship: all expenses linked to this grant
    expenses = relationship(
        "Expense",
        back_populates="grant",
        cascade="all, delete-orphan",
    )

    # Relationship: student enrollments for compliance tracking
    enrollments = relationship(
        "GrantEnrollment",
        back_populates="grant",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_grant_dates", "start_date", "end_date"),
        Index("ix_grant_active", "is_active"),
    )

    @property
    def remaining_amount(self) -> Numeric:
        """Calculate remaining budget."""
        spent = self.spent_amount or 0
        return self.total_amount - spent

    @property
    def utilization_percent(self) -> float:
        """Calculate budget utilization percentage."""
        if self.total_amount == 0:
            return 0.0
        spent = float(self.spent_amount or 0)
        return (spent / float(self.total_amount)) * 100

    def __repr__(self):
        return f"<Grant(id={self.id}, name='{self.name}', total={self.total_amount})>"
