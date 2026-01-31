"""
Instructor model for tracking teaching staff.
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, Enum, Index
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import RateType


class Instructor(TimestampMixin, SoftDeleteMixin, Base):
    """
    Represents an instructor who teaches in the IP2A program.

    Tracks contact info, certifications, pay rates, and tax classification.
    Uses Association Object pattern for cohort assignments to maintain
    full audit trail of teaching assignments.
    """

    __tablename__ = "instructors"

    id = Column(Integer, primary_key=True, index=True)

    # Identity
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(50), nullable=True)

    # Professional info
    bio = Column(Text, nullable=True)
    certification = Column(String(255), nullable=True)
    specialties = Column(Text, nullable=True)  # Comma-separated or JSON

    # Pay rate configuration
    rate_type = Column(
        Enum(RateType, name="rate_type", create_constraint=True),
        nullable=False,
        default=RateType.HOURLY,
    )
    rate_amount = Column(Numeric(10, 2), nullable=True)  # Default rate

    # Tax classification
    is_contractor_1099 = Column(Boolean, default=False, nullable=False)
    tax_id = Column(String(20), nullable=True)  # EIN or SSN (encrypted in production)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Cohort assignments via Association Object
    # This replaces the simple many-to-many with full tracking
    cohort_assignments = relationship(
        "InstructorCohortAssignment",
        back_populates="instructor",
        cascade="all, delete-orphan",
    )

    # One-to-many: logged hour entries
    hours_entries = relationship(
        "InstructorHours",
        back_populates="instructor",
        cascade="all, delete-orphan",
    )

    # NOTE: Commented out due to conflict with Phase 2 Training System
    # The new training system ClassSession model doesn't relate to Instructor.
    # class_sessions = relationship(
    #     "ClassSession",
    #     back_populates="instructor",
    # )

    __table_args__ = (
        Index("ix_instructor_name", "last_name", "first_name"),
        Index("ix_instructor_active", "is_active"),
    )

    # Convenience properties
    @property
    def full_name(self) -> str:
        """Return instructor's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def cohorts(self):
        """Get all active (non-deleted) cohort assignments."""
        return [
            assignment.cohort
            for assignment in self.cohort_assignments
            if not assignment.is_deleted
        ]

    def __repr__(self):
        return (
            f"<Instructor(id={self.id}, name='{self.full_name}', email='{self.email}')>"
        )
