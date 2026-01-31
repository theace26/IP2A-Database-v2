"""
Instructor hours tracking model.
"""

from sqlalchemy import Column, Integer, Date, Numeric, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin


class InstructorHours(TimestampMixin, SoftDeleteMixin, Base):
    """
    Tracks hours worked by instructors.

    Links to instructor, location, and optionally cohort.
    Supports prep time tracking and payroll-ready calculations.
    """

    __tablename__ = "instructor_hours"

    id = Column(Integer, primary_key=True, index=True)

    # Required links
    instructor_id = Column(
        Integer,
        ForeignKey("instructors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Optional links
    location_id = Column(
        Integer,
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    cohort_id = Column(
        Integer,
        ForeignKey("cohorts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Time tracking
    date = Column(Date, nullable=False, index=True)
    hours = Column(Numeric(5, 2), nullable=False)  # Teaching hours
    prep_hours = Column(Numeric(5, 2), nullable=True, default=0)  # Prep time

    # Computed field (can be calculated: hours + prep_hours)
    # Stored for reporting convenience
    total_hours = Column(Numeric(6, 2), nullable=True)

    # Rate override (if different from instructor's default rate)
    rate_override = Column(Numeric(10, 2), nullable=True)

    # Payroll tracking
    is_paid = Column(Boolean, default=False, nullable=False, index=True)
    paid_date = Column(Date, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    instructor = relationship("Instructor", back_populates="hours_entries")
    location = relationship("Location", back_populates="instructor_hours")
    cohort = relationship("Cohort", back_populates="instructor_hours")

    __table_args__ = (
        Index("ix_instructor_hours_date_range", "instructor_id", "date"),
        Index("ix_instructor_hours_unpaid", "is_paid", "instructor_id"),
    )

    def calculate_total(self) -> Numeric:
        """Calculate and return total hours (teaching + prep)."""
        prep = self.prep_hours or 0
        return self.hours + prep

    def __repr__(self):
        return f"<InstructorHours(id={self.id}, instructor={self.instructor_id}, date={self.date}, hours={self.hours})>"
