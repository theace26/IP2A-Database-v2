"""DuesRate model for dues rate schedules."""

from sqlalchemy import Column, Integer, String, Date, Numeric, Enum as SAEnum, UniqueConstraint

from src.db.base import Base
from src.db.mixins import TimestampMixin
from src.db.enums import MemberClassification


class DuesRate(Base, TimestampMixin):
    """Dues rate schedule by member classification."""

    __tablename__ = "dues_rates"

    id = Column(Integer, primary_key=True, index=True)
    classification = Column(SAEnum(MemberClassification), nullable=False)
    monthly_amount = Column(Numeric(10, 2), nullable=False)
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # NULL = currently active
    description = Column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint('classification', 'effective_date', name='uq_dues_rate_class_effective'),
    )

    def __repr__(self):
        return f"<DuesRate(id={self.id}, class='{self.classification.value}', amount=${self.monthly_amount})>"
