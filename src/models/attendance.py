"""Attendance model for class sessions."""

from datetime import time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Integer,
    Time,
    Text,
    ForeignKey,
    Enum as SQLEnum,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin
from src.db.enums import SessionAttendanceStatus

if TYPE_CHECKING:
    from src.models.student import Student
    from src.models.class_session import ClassSession


class Attendance(Base, TimestampMixin):
    """
    Attendance record for a student at a class session.
    """

    __tablename__ = "attendances"

    __table_args__ = (
        UniqueConstraint("student_id", "class_session_id", name="uq_student_session"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    class_session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("class_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Attendance status
    status: Mapped[SessionAttendanceStatus] = mapped_column(
        SQLEnum(SessionAttendanceStatus, name="session_attendance_status_enum"),
        nullable=False,
        index=True,
    )

    # Time tracking (for late arrivals / early departures)
    arrival_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    departure_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student", back_populates="attendances", lazy="joined"
    )

    class_session: Mapped["ClassSession"] = relationship(
        "ClassSession", back_populates="attendances", lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<Attendance(student_id={self.student_id}, session_id={self.class_session_id}, status={self.status})>"
