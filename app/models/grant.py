from sqlalchemy import Column, Integer, String, Date, Numeric, Boolean, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class Grant(Base):
    __tablename__ = "grants"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False)
    funding_source = Column(String(255), nullable=True)

    total_amount = Column(Numeric(12, 2), nullable=False)
    spent_amount = Column(Numeric(12, 2), nullable=True)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    # JSON or comma-separated list of categories
    allowable_categories = Column(Text, nullable=True)

    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationship: all expenses linked to this grant
    expenses = relationship("Expense", back_populates="grant")
