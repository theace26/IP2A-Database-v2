"""Grievance model for formal complaint tracking."""

from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, Numeric, Enum as SAEnum
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import GrievanceStep, GrievanceStatus, GrievanceStepOutcome


class Grievance(Base, TimestampMixin, SoftDeleteMixin):
    """Formal complaint tracking through arbitration."""

    __tablename__ = "grievances"

    id = Column(Integer, primary_key=True, index=True)

    # Unique grievance identifier
    grievance_number = Column(String(20), unique=True, nullable=False, index=True)

    # Parties
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    employer_id = Column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )

    # Filing details
    filed_date = Column(Date, nullable=False)
    incident_date = Column(Date)
    contract_article = Column(String(50))
    violation_description = Column(Text, nullable=False)
    remedy_sought = Column(Text)

    # Current state
    current_step = Column(
        SAEnum(GrievanceStep), default=GrievanceStep.STEP_1, nullable=False
    )
    status = Column(
        SAEnum(GrievanceStatus), default=GrievanceStatus.OPEN, nullable=False, index=True
    )
    assigned_rep = Column(String(100))

    # Resolution
    resolution = Column(Text)
    resolution_date = Column(Date)
    settlement_amount = Column(Numeric(10, 2))

    # Notes
    notes = Column(Text)

    # Relationships
    member = relationship("Member", backref="grievances")
    employer = relationship("Organization", backref="grievances")
    steps = relationship("GrievanceStepRecord", back_populates="grievance")

    def __repr__(self):
        return f"<Grievance(id={self.id}, number='{self.grievance_number}', status='{self.status}')>"


class GrievanceStepRecord(Base, TimestampMixin):
    """Record of a specific step meeting in the grievance process."""

    __tablename__ = "grievance_step_records"

    id = Column(Integer, primary_key=True, index=True)

    # Which grievance
    grievance_id = Column(
        Integer, ForeignKey("grievances.id"), nullable=False, index=True
    )

    # Step details
    step_number = Column(Integer, nullable=False)
    meeting_date = Column(Date, nullable=False)
    union_attendees = Column(Text)
    employer_attendees = Column(Text)
    outcome = Column(SAEnum(GrievanceStepOutcome), nullable=False)
    notes = Column(Text)

    # Relationships
    grievance = relationship("Grievance", back_populates="steps")

    def __repr__(self):
        return f"<GrievanceStepRecord(id={self.id}, grievance_id={self.grievance_id}, step={self.step_number})>"
