"""Enrollment model - student enrollment in courses."""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, Date, Float, Text, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin
from src.db.enums import CourseEnrollmentStatus

if TYPE_CHECKING:
    from src.models.student import Student
    from src.models.course import Course


class Enrollment(Base, TimestampMixin):
    """
    Student enrollment in a course.

    Tracks when a student enrolled, their status, and final grade.
    """

    __tablename__ = "enrollments"

    __table_args__ = (
        # Student can only enroll in a course once per cohort/term
        UniqueConstraint("student_id", "course_id", "cohort", name="uq_student_course_cohort"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Enrollment details
    cohort: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "2026-Spring"
    enrollment_date: Mapped[date] = mapped_column(Date, nullable=False)
    completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Status
    status: Mapped[CourseEnrollmentStatus] = mapped_column(
        SQLEnum(CourseEnrollmentStatus, name="course_enrollment_status_enum"),
        default=CourseEnrollmentStatus.ENROLLED,
        nullable=False,
        index=True
    )

    # Final grade
    final_grade: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    letter_grade: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)  # A, B+, etc.

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="enrollments",
        lazy="joined"
    )

    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="enrollments",
        lazy="joined"
    )

    @property
    def is_passing(self) -> Optional[bool]:
        """Check if student is passing based on final grade."""
        if self.final_grade is None:
            return None
        return self.final_grade >= self.course.passing_grade

    def __repr__(self) -> str:
        return f"<Enrollment(id={self.id}, student_id={self.student_id}, course_id={self.course_id})>"
