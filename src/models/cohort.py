"""
Cohort model for grouping students in training programs.
"""

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, Text, Index
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import CohortStatus


class Cohort(TimestampMixin, SoftDeleteMixin, Base):
    """
    Represents a cohort/class of students in the IP2A program.

    A cohort has a defined start/end date, location, and assigned instructors.
    Uses Association Object pattern for instructor relationships to track
    assignment history and primary instructor designation.
    """

    __tablename__ = "cohorts"

    id = Column(Integer, primary_key=True, index=True)

    # Identity
    name = Column(String(100), nullable=False)
    code = Column(
        String(50), nullable=True, unique=True, index=True
    )  # e.g., "IP2A-2025-Q1"
    description = Column(Text, nullable=True)

    # Status tracking
    status = Column(
        Enum(CohortStatus, name="cohort_status", create_constraint=True),
        nullable=False,
        default=CohortStatus.PLANNED,
        index=True,
    )

    # Dates
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True)

    # Capacity
    max_students = Column(Integer, nullable=True)

    # Location assignment
    location_id = Column(
        Integer,
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    location = relationship("Location", back_populates="cohorts")

    # Instructor assignments via Association Object
    # This replaces the simple many-to-many with full tracking
    instructor_assignments = relationship(
        "InstructorCohortAssignment",
        back_populates="cohort",
        cascade="all, delete-orphan",
    )

    # Students in this cohort
    students = relationship(
        "Student",
        back_populates="cohort",
        cascade="all, delete-orphan",
    )

    # Class sessions
    class_sessions = relationship(
        "ClassSession",
        back_populates="cohort",
        cascade="all, delete-orphan",
    )

    # Instructor hours logged against this cohort
    instructor_hours = relationship(
        "InstructorHours",
        back_populates="cohort",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("ix_cohort_dates", "start_date", "end_date"),)

    # Convenience properties
    @property
    def instructors(self):
        """Get all active (non-deleted) instructors for this cohort."""
        return [
            assignment.instructor
            for assignment in self.instructor_assignments
            if not assignment.is_deleted
        ]

    @property
    def primary_instructor(self):
        """Get the primary instructor for this cohort, if designated."""
        for assignment in self.instructor_assignments:
            if assignment.is_primary and not assignment.is_deleted:
                return assignment.instructor
        return None

    def __repr__(self):
        return f"<Cohort(id={self.id}, name='{self.name}', status={self.status})>"
