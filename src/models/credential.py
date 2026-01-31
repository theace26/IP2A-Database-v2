"""
Credential model for tracking student certifications and qualifications.
"""

from typing import Optional

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import CredentialStatus


class Credential(TimestampMixin, SoftDeleteMixin, Base):
    """
    Tracks credentials, certifications, and qualifications earned by students.

    Examples: OSHA 10, First Aid/CPR, Forklift certification, etc.
    Supports expiration tracking and status management.
    """

    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Credential details
    credential_name = Column(String(255), nullable=False, index=True)
    issuing_org = Column(String(255), nullable=True)
    certificate_number = Column(String(255), nullable=True)

    # Dates
    issue_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=True, index=True)

    # Status tracking
    status = Column(
        Enum(CredentialStatus, name="credential_status", create_constraint=True),
        nullable=False,
        default=CredentialStatus.ACTIVE,
        index=True,
    )

    notes = Column(Text, nullable=True)

    # File attachment
    attachment_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationship
    # OLD SYSTEM - student = relationship("Student", back_populates="credentials")

    __table_args__ = (
        Index("ix_credential_student_name", "student_id", "credential_name"),
        Index("ix_credential_expiration", "expiration_date"),
    )

    @property
    def is_expired(self) -> bool:
        """Check if credential has expired."""
        from datetime import date

        if self.expiration_date is None:
            return False
        return self.expiration_date < date.today()

    def __repr__(self):
        return f"<Credential(id={self.id}, name='{self.credential_name}', student={self.student_id})>"
