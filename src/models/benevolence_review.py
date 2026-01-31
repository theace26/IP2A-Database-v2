"""Benevolence review model for multi-level approval workflow."""

from sqlalchemy import Column, Integer, Date, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin
from src.db.enums import BenevolenceReviewLevel, BenevolenceReviewDecision


class BenevolenceReview(Base, TimestampMixin):
    """A single review step in the benevolence approval workflow."""

    __tablename__ = "benevolence_reviews"

    id = Column(Integer, primary_key=True, index=True)

    # Which application
    application_id = Column(
        Integer,
        ForeignKey("benevolence_applications.id"),
        nullable=False,
        index=True,
    )

    # Reviewer info
    reviewer_name = Column(Text, nullable=False)
    review_level = Column(SAEnum(BenevolenceReviewLevel), nullable=False)

    # Decision
    decision = Column(SAEnum(BenevolenceReviewDecision), nullable=False)
    review_date = Column(Date, nullable=False)
    comments = Column(Text)

    # Relationships
    application = relationship("BenevolenceApplication", back_populates="reviews")

    def __repr__(self):
        return f"<BenevolenceReview(id={self.id}, level='{self.review_level}', decision='{self.decision}')>"
