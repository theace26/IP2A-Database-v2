from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys (optional)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    grant_id = Column(Integer, ForeignKey("grants.id"), nullable=True)

    # Core expense details
    item = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)

    # Optional charge modifiers
    tax = Column(Numeric(10, 2), nullable=True)
    discount = Column(Numeric(10, 2), nullable=True)

    category = Column(String(100), nullable=True)
    vendor = Column(String(255), nullable=True)

    purchased_at = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    student = relationship("Student", backref="expenses")
    location = relationship("Location", backref="expenses")
    grant = relationship("Grant", back_populates="expenses")
