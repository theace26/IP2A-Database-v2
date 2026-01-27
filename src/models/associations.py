"""
Association models for many-to-many relationships in the IP2A Database.

Using Association Object pattern instead of simple join tables to support:
- Audit trail (created_at, updated_at)
- Soft delete (preserve historical assignments)
- Additional metadata on relationships
"""

from sqlalchemy import Column, Integer, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin


class InstructorCohortAssignment(TimestampMixin, SoftDeleteMixin, Base):
    """
    Tracks instructor assignments to cohorts.

    Replaces simple many-to-many join table to support full audit trail
    and soft delete capability.
    """

    __tablename__ = "instructor_cohort"

    # Composite primary key
    instructor_id = Column(
        Integer,
        ForeignKey("instructors.id", ondelete="CASCADE"),
        primary_key=True,
    )
    cohort_id = Column(
        Integer,
        ForeignKey("cohorts.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Assignment metadata
    is_primary = Column(Boolean, default=False, nullable=False)

    # Relationships
    instructor = relationship("Instructor", back_populates="cohort_assignments")
    cohort = relationship("Cohort", back_populates="instructor_assignments")

    __table_args__ = (
        Index("ix_instructor_cohort_instructor", "instructor_id"),
        Index("ix_instructor_cohort_cohort", "cohort_id"),
    )

    def __repr__(self):
        return f"<InstructorCohortAssignment(instructor={self.instructor_id}, cohort={self.cohort_id}, primary={self.is_primary})>"
