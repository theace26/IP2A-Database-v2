"""Student model for pre-apprenticeship program."""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, Date, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import StudentStatus

if TYPE_CHECKING:
    from src.models.member import Member
    from src.models.enrollment import Enrollment
    from src.models.grade import Grade
    from src.models.certification import Certification
    from src.models.attendance import Attendance


class Student(Base, TimestampMixin, SoftDeleteMixin):
    """
    Student in the pre-apprenticeship program.

    A Student is linked to a Member record. Not all Members are Students,
    but all Students should have a Member record.
    """

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Link to Member (required)
    member_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("members.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,  # One student record per member
        index=True,
    )

    # Student-specific fields
    student_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )

    status: Mapped[StudentStatus] = mapped_column(
        SQLEnum(StudentStatus, name="student_status_enum"),
        default=StudentStatus.APPLICANT,
        nullable=False,
        index=True,
    )

    # Program dates
    application_date: Mapped[date] = mapped_column(Date, nullable=False)
    enrollment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expected_completion_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )
    actual_completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Program info
    cohort: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # e.g., "2026-Spring"

    # Emergency contact
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True
    )
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    emergency_contact_relationship: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    member: Mapped["Member"] = relationship(
        "Member", back_populates="student", lazy="joined"
    )

    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="student",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    grades: Mapped[list["Grade"]] = relationship(
        "Grade", back_populates="student", lazy="selectin", cascade="all, delete-orphan"
    )

    certifications: Mapped[list["Certification"]] = relationship(
        "Certification",
        back_populates="student",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    attendances: Mapped[list["Attendance"]] = relationship(
        "Attendance",
        back_populates="student",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def full_name(self) -> str:
        """Get student's full name from member."""
        return f"{self.member.first_name} {self.member.last_name}"

    @property
    def is_active(self) -> bool:
        """Check if student is currently active in program."""
        return self.status in [StudentStatus.ENROLLED, StudentStatus.ON_LEAVE]

    def __repr__(self) -> str:
        return f"<Student(id={self.id}, number='{self.student_number}', status={self.status})>"
