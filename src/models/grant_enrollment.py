"""
Grant enrollment model for tracking student participation in grants.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    Text,
    Enum,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import GrantEnrollmentStatus, GrantOutcome


class GrantEnrollment(TimestampMixin, SoftDeleteMixin, Base):
    """
    Links students to grants with outcome tracking.

    Tracks enrollment status, completion, and placement outcomes
    for grant compliance reporting.
    """

    __tablename__ = "grant_enrollments"
    __table_args__ = (
        UniqueConstraint("grant_id", "student_id", name="uq_grant_student"),
        Index("ix_grant_enrollment_status", "grant_id", "status"),
        Index("ix_grant_enrollment_outcome", "grant_id", "outcome"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    grant_id = Column(
        Integer,
        ForeignKey("grants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Enrollment tracking
    enrollment_date = Column(Date, nullable=False, index=True)
    status = Column(
        Enum(GrantEnrollmentStatus, name="grant_enrollment_status", create_constraint=True),
        nullable=False,
        default=GrantEnrollmentStatus.ENROLLED,
    )

    # Completion tracking
    completion_date = Column(Date, nullable=True)

    # Outcome tracking (for compliance reporting)
    outcome = Column(
        Enum(GrantOutcome, name="grant_outcome", create_constraint=True),
        nullable=True,
    )
    outcome_date = Column(Date, nullable=True)

    # Placement tracking (if job placement is a metric)
    placement_employer = Column(String(200), nullable=True)
    placement_date = Column(Date, nullable=True)
    placement_wage = Column(String(50), nullable=True)  # e.g., "$18.50/hr"
    placement_job_title = Column(String(200), nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    grant = relationship("Grant", back_populates="enrollments")
    student = relationship("Student", back_populates="grant_enrollments")

    def __repr__(self):
        return (
            f"<GrantEnrollment(id={self.id}, grant={self.grant_id}, "
            f"student={self.student_id}, status={self.status})>"
        )
