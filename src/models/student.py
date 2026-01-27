"""
Student model - core entity for program participants.
"""

from sqlalchemy import Column, Integer, String, Date, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin


class Student(TimestampMixin, SoftDeleteMixin, Base):
    """
    Represents a student in the IP2A program.

    Core entity that links to credentials, tools, applications, attendance, etc.
    Uses JSON 'extra' field for flexible extension without schema changes.
    """

    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)

    # Core identity
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    middle_name = Column(String(50), nullable=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(50), nullable=True)
    birthdate = Column(Date, nullable=True)

    # Full address structure
    address_line1 = Column(String(200), nullable=True)
    address_line2 = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    postal_code = Column(String(20), nullable=True)

    # Legacy single address field (for backward compatibility)
    address = Column(String(255), nullable=True)

    # Program-specific fields
    shoe_size = Column(String(16), nullable=True)
    shirt_size = Column(String(16), nullable=True)
    profile_photo_path = Column(String(500), nullable=True)

    # Emergency contact
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(50), nullable=True)
    emergency_contact_relation = Column(String(50), nullable=True)

    # Flexible extension field for custom data
    # Example: {"veteran": true, "referred_by": "John Smith", "languages": ["English", "Spanish"]}
    extra = Column(JSON, nullable=True)

    # Cohort assignment
    cohort_id = Column(
        Integer,
        ForeignKey("cohorts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    cohort = relationship("Cohort", back_populates="students")

    # Related records
    credentials = relationship(
        "Credential",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    tools_issued = relationship(
        "ToolsIssued",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    jatc_applications = relationship(
        "JATCApplication",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    attendance_records = relationship(
        "Attendance",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    expenses = relationship(
        "Expense",
        back_populates="student",
    )

    __table_args__ = (
        Index("ix_student_name", "last_name", "first_name"),
        Index("ix_student_city_state", "city", "state"),
    )

    @property
    def full_name(self) -> str:
        """Return student's full name."""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    @property
    def full_address(self) -> str:
        """Return formatted full address."""
        parts = []
        if self.address_line1:
            parts.append(self.address_line1)
        if self.address_line2:
            parts.append(self.address_line2)
        city_state_zip = []
        if self.city:
            city_state_zip.append(self.city)
        if self.state:
            city_state_zip.append(self.state)
        if self.postal_code:
            city_state_zip.append(self.postal_code)
        if city_state_zip:
            parts.append(", ".join(city_state_zip))
        return "\n".join(parts) if parts else ""

    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.full_name}', email='{self.email}')>"
