"""Course model for training program."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, Text, Boolean, Float, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import CourseType

if TYPE_CHECKING:
    from src.models.class_session import ClassSession
    from src.models.enrollment import Enrollment
    from src.models.grade import Grade


class Course(Base, TimestampMixin, SoftDeleteMixin):
    """
    Course in the pre-apprenticeship curriculum.

    Courses are reusable templates. ClassSessions are specific
    instances of courses with dates and instructors.
    """

    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Course identification
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Course type
    course_type: Mapped[CourseType] = mapped_column(
        SQLEnum(CourseType, name="course_type_enum"),
        default=CourseType.CORE,
        nullable=False
    )

    # Requirements
    credits: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    hours: Mapped[int] = mapped_column(Integer, default=40, nullable=False)  # Total contact hours
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Grading
    passing_grade: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)

    # Prerequisites (comma-separated course codes)
    prerequisites: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Active status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    class_sessions: Mapped[list["ClassSession"]] = relationship(
        "ClassSession",
        back_populates="course",
        lazy="selectin"
    )

    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="course",
        lazy="selectin"
    )

    grades: Mapped[list["Grade"]] = relationship(
        "Grade",
        back_populates="course",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Course(id={self.id}, code='{self.code}', name='{self.name}')>"
