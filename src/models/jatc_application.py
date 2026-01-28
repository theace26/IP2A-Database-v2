"""
JATC Application model for tracking apprenticeship applications.
"""

from typing import Optional

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin


class JATCApplication(TimestampMixin, SoftDeleteMixin, Base):
    """
    Tracks JATC (Joint Apprenticeship and Training Committee) applications.

    Records the application process from submission through interview
    to final decision for students applying to apprenticeship programs.
    """

    __tablename__ = "jatc_applications"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Application timeline
    application_date = Column(Date, nullable=False, index=True)
    interview_date = Column(Date, nullable=True, index=True)
    decision_date = Column(Date, nullable=True)

    # Status: pending, interview_scheduled, interviewed, accepted, rejected, waitlisted
    status = Column(String(50), nullable=False, default="pending", index=True)

    # Interview/evaluation scores (optional)
    interview_score = Column(Numeric(5, 2), nullable=True)
    aptitude_score = Column(Numeric(5, 2), nullable=True)
    math_score = Column(Numeric(5, 2), nullable=True)
    reading_score = Column(Numeric(5, 2), nullable=True)

    # Application details
    trade_preference = Column(String(100), nullable=True)  # Electrician, etc.
    local_applied = Column(String(50), nullable=True)  # IBEW Local number

    notes = Column(Text, nullable=True)

    # Supporting documents
    supporting_docs_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # NOTE: Commented out due to conflict with Phase 2 Training System
    # The new training system Student model doesn't have jatc_applications relationship.
    # student = relationship(
    #     "Student",
    #     back_populates="jatc_applications",
    # )

    __table_args__ = (
        Index("ix_jatc_student_status", "student_id", "status"),
        Index("ix_jatc_dates", "application_date", "interview_date"),
    )

    def __repr__(self):
        return f"<JATCApplication(id={self.id}, student={self.student_id}, status='{self.status}')>"
