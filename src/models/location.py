"""
Location model for training sites and facilities.
"""

from sqlalchemy import Column, Integer, String, Text, Enum, Index
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import LocationType


class Location(TimestampMixin, SoftDeleteMixin, Base):
    """
    Represents a physical location used for training.

    Can be a training site, school, office, jobsite, etc.
    Tracks full address and capacity information.
    """

    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)

    # Identity
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=True, unique=True)  # Short code for reports

    # Type classification
    type = Column(
        Enum(LocationType, name="location_type", create_constraint=True),
        nullable=False,
        default=LocationType.TRAINING_SITE,
        index=True,
    )

    # Full address structure
    address_line1 = Column(String(200), nullable=True)
    address_line2 = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True, index=True)
    state = Column(String(50), nullable=True, index=True)
    postal_code = Column(String(20), nullable=True)

    # Legacy single address field (for backward compatibility)
    address = Column(String(255), nullable=True)

    # Facility details
    capacity = Column(Integer, nullable=True)
    square_footage = Column(Integer, nullable=True)

    # Contact info
    contact_name = Column(String(100), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contact_email = Column(String(255), nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    cohorts = relationship("Cohort", back_populates="location")
    instructor_hours = relationship(
        "InstructorHours",
        back_populates="location",
        cascade="all, delete-orphan",
    )
    class_sessions = relationship(
        "ClassSession",
        back_populates="location",
    )
    expenses = relationship(
        "Expense",
        back_populates="location",
    )

    __table_args__ = (Index("ix_location_city_state", "city", "state"),)

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
        return f"<Location(id={self.id}, name='{self.name}', type={self.type})>"
