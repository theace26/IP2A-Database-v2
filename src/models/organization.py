"""Organization model for employers, unions, training partners."""

from sqlalchemy import Column, Integer, String, Text, Enum as SAEnum
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import OrganizationType, SaltingScore


class Organization(Base, TimestampMixin, SoftDeleteMixin):
    """Organization entity - employers, unions, training partners, JATC."""

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    org_type = Column(SAEnum(OrganizationType), nullable=False)

    # Address
    address = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))

    # Contact
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))

    # SALTing specific (for employers)
    salting_score = Column(SAEnum(SaltingScore), nullable=True)
    salting_notes = Column(Text, nullable=True)

    # Relationships
    contacts = relationship("OrganizationContact", back_populates="organization")
    member_employments = relationship("MemberEmployment", back_populates="organization")

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}', type={self.org_type})>"
