"""MemberEmployment model - tracks member work history at organizations."""

from sqlalchemy import Column, Integer, ForeignKey, Date, Numeric, Boolean, String
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin


class MemberEmployment(Base, TimestampMixin):
    """Association: Member employment history at organizations."""

    __tablename__ = "member_employments"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # NULL = currently employed

    job_title = Column(String(100))
    hourly_rate = Column(Numeric(10, 2))
    is_current = Column(Boolean, default=True)

    # Relationships
    member = relationship("Member", back_populates="employments")
    organization = relationship("Organization", back_populates="member_employments")

    def __repr__(self):
        return f"<MemberEmployment(member_id={self.member_id}, org_id={self.organization_id})>"
