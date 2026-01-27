"""
Class session model for tracking individual training sessions.
"""

from sqlalchemy import Column, Integer, Date, Time, ForeignKey, String, Text, Index
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin


class ClassSession(TimestampMixin, SoftDeleteMixin, Base):
    """
    Represents a single class/training session.

    Links cohort, instructor, and location for a specific date/time.
    Attendance records are tracked separately per student.
    """

    __tablename__ = "class_sessions"

    id = Column(Integer, primary_key=True, index=True)

    cohort_id = Column(
        Integer,
        ForeignKey("cohorts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    instructor_id = Column(
        Integer,
        ForeignKey("instructors.id", ondelete="SET NULL"),
        nullable=True,  # Allow null if instructor removed
        index=True,
    )
    location_id = Column(
        Integer,
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Session timing
    date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)

    # Session content
    topic = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    cohort = relationship("Cohort", back_populates="class_sessions")
    instructor = relationship("Instructor", back_populates="class_sessions")
    location = relationship("Location", back_populates="class_sessions")
    attendance_records = relationship(
        "Attendance",
        back_populates="class_session",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("ix_class_session_date_cohort", "date", "cohort_id"),)

    def __repr__(self):
        return (
            f"<ClassSession(id={self.id}, date={self.date}, cohort={self.cohort_id})>"
        )
