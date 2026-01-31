"""OrganizationContact model for people at organizations."""

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin


class OrganizationContact(Base, TimestampMixin, SoftDeleteMixin):
    """Contact person at an organization."""

    __tablename__ = "organization_contacts"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    title = Column(String(100))

    phone = Column(String(50))
    email = Column(String(255))

    is_primary = Column(Boolean, default=False)
    notes = Column(String(500))

    # Relationships
    organization = relationship("Organization", back_populates="contacts")

    def __repr__(self):
        return f"<OrganizationContact(id={self.id}, name='{self.first_name} {self.last_name}')>"
