"""Certification model for student certifications."""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, Date, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin
from src.db.enums import CertificationType, CertificationStatus

if TYPE_CHECKING:
    from src.models.student import Student


class Certification(Base, TimestampMixin):
    """
    Certification earned by a student.

    Tracks OSHA, first aid, and other certifications
    required or earned during the program.
    """

    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Certification type
    cert_type: Mapped[CertificationType] = mapped_column(
        SQLEnum(CertificationType, name="certification_type_enum"),
        nullable=False,
        index=True
    )

    # For custom certifications
    custom_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Status
    status: Mapped[CertificationStatus] = mapped_column(
        SQLEnum(CertificationStatus, name="certification_status_enum"),
        default=CertificationStatus.PENDING,
        nullable=False,
        index=True
    )

    # Dates
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Certificate details
    certificate_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    issuing_organization: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Verification
    verified_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    verification_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="certifications",
        lazy="joined"
    )

    @property
    def display_name(self) -> str:
        """Get display name for certification."""
        if self.cert_type == CertificationType.OTHER and self.custom_name:
            return self.custom_name
        return self.cert_type.value.replace("_", " ").title()

    @property
    def is_expired(self) -> bool:
        """Check if certification has expired."""
        if not self.expiration_date:
            return False
        return date.today() > self.expiration_date

    @property
    def is_valid(self) -> bool:
        """Check if certification is currently valid."""
        return self.status == CertificationStatus.ACTIVE and not self.is_expired

    def __repr__(self) -> str:
        return f"<Certification(id={self.id}, student_id={self.student_id}, type={self.cert_type})>"
