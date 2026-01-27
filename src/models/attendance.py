"""
Attendance tracking for class sessions.
"""

from sqlalchemy import Column, Integer, ForeignKey, Text, UniqueConstraint, Enum, Index
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import AttendanceStatus


class Attendance(TimestampMixin, SoftDeleteMixin, Base):
    """
    Records student attendance for individual class sessions.

    Uses enum for status to ensure data integrity.
    Soft delete allows correcting mistakes without losing history.
    """

    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    class_session_id = Column(
        Integer,
        ForeignKey("class_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Using enum for data integrity
    status = Column(
        Enum(AttendanceStatus, name="attendance_status", create_constraint=True),
        nullable=False,
        default=AttendanceStatus.PRESENT,
    )

    # Only relevant if late
    minutes_late = Column(Integer, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="attendance_records")
    class_session = relationship("ClassSession", back_populates="attendance_records")

    __table_args__ = (
        # Prevent duplicate attendance entries for the same session
        UniqueConstraint("student_id", "class_session_id", name="uq_student_session"),
        Index("ix_attendance_status", "status"),
    )

    def __repr__(self):
        return f"<Attendance(student={self.student_id}, session={self.class_session_id}, status={self.status})>"
