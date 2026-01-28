"""Class session model - specific instances of courses."""

from datetime import date, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, Date, Time, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.models.course import Course
    from src.models.attendance import Attendance


class ClassSession(Base, TimestampMixin):
    """
    A specific class session - one meeting of a course.

    Multiple ClassSessions make up a course offering.
    Attendance is tracked per ClassSession.
    """

    __tablename__ = "class_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Link to course
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Session details
    session_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    # Location
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    room: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Instructor
    instructor_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Session info
    topic: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True
    )

    # Relationships
    course: Mapped["Course"] = relationship(
        "Course", back_populates="class_sessions", lazy="joined"
    )

    attendances: Mapped[list["Attendance"]] = relationship(
        "Attendance",
        back_populates="class_session",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def duration_hours(self) -> float:
        """Calculate session duration in hours."""
        from datetime import datetime

        start = datetime.combine(self.session_date, self.start_time)
        end = datetime.combine(self.session_date, self.end_time)
        return (end - start).seconds / 3600

    def __repr__(self) -> str:
        return f"<ClassSession(id={self.id}, course_id={self.course_id}, date={self.session_date})>"
