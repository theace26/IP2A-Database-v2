"""SALTing activity model for tracking union organizing efforts."""

from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import SALTingActivityType, SALTingOutcome


class SALTingActivity(Base, TimestampMixin, SoftDeleteMixin):
    """Tracks organizing activities at non-union employers."""

    __tablename__ = "salting_activities"

    id = Column(Integer, primary_key=True, index=True)

    # Who performed the activity
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)

    # Target employer
    organization_id = Column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )

    # Activity details
    activity_type = Column(
        SAEnum(SALTingActivityType), nullable=False
    )
    activity_date = Column(Date, nullable=False)
    outcome = Column(SAEnum(SALTingOutcome), nullable=True)

    # Details
    location = Column(String(255))
    workers_contacted = Column(Integer, default=0)
    cards_signed = Column(Integer, default=0)
    description = Column(Text)
    notes = Column(Text)

    # Relationships
    member = relationship("Member", backref="salting_activities")
    organization = relationship("Organization", backref="salting_activities")

    def __repr__(self):
        return f"<SALTingActivity(id={self.id}, type='{self.activity_type}', date='{self.activity_date}')>"
