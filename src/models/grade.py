"""Grade model for student assessments."""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, Date, Float, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin
from src.db.enums import GradeType

if TYPE_CHECKING:
    from src.models.student import Student
    from src.models.course import Course


class Grade(Base, TimestampMixin):
    """
    Individual grade/assessment for a student in a course.

    Multiple grades per student per course are expected
    (assignments, quizzes, exams, etc.).
    """

    __tablename__ = "grades"

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

    # Grade details
    grade_type: Mapped[GradeType] = mapped_column(
        SQLEnum(GradeType, name="grade_type_enum"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)  # e.g., "Week 3 Quiz"

    # Scoring
    points_earned: Mapped[float] = mapped_column(Float, nullable=False)
    points_possible: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)  # For weighted grades

    # Date
    grade_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Feedback
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Who graded
    graded_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="grades",
        lazy="joined"
    )

    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="grades",
        lazy="joined"
    )

    @property
    def percentage(self) -> float:
        """Calculate percentage score."""
        if self.points_possible == 0:
            return 0.0
        return (self.points_earned / self.points_possible) * 100

    @property
    def letter_grade(self) -> str:
        """Convert percentage to letter grade."""
        pct = self.percentage
        if pct >= 90:
            return "A"
        elif pct >= 80:
            return "B"
        elif pct >= 70:
            return "C"
        elif pct >= 60:
            return "D"
        else:
            return "F"

    def __repr__(self) -> str:
        return f"<Grade(id={self.id}, student_id={self.student_id}, name='{self.name}')>"
