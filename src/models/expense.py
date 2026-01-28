"""
Expense tracking model for program purchases and costs.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Numeric,
    ForeignKey,
    Text,
    Enum,
    Index,
)
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import PaymentMethod


class Expense(TimestampMixin, SoftDeleteMixin, Base):
    """
    Tracks program expenses and purchases.

    Can be linked to students (individual supplies), locations (facility costs),
    or grants (for grant reporting and compliance).
    """

    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys (all optional - expense may or may not be linked)
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    location_id = Column(
        Integer,
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    grant_id = Column(
        Integer,
        ForeignKey("grants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Core expense details
    item = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)

    # Optional charge modifiers
    tax = Column(Numeric(10, 2), nullable=True)
    discount = Column(Numeric(10, 2), nullable=True)

    # Categorization
    category = Column(String(100), nullable=True, index=True)
    vendor = Column(String(255), nullable=True)

    # Payment info
    payment_method = Column(
        Enum(PaymentMethod, name="payment_method", create_constraint=True),
        nullable=True,
    )
    receipt_number = Column(String(100), nullable=True)
    receipt_path = Column(String(500), nullable=True)

    # Date tracking
    purchased_at = Column(Date, nullable=False, index=True)

    notes = Column(Text, nullable=True)

    # Relationships
    # OLD SYSTEM - student = relationship("Student", back_populates="expenses")
    location = relationship("Location", back_populates="expenses")
    grant = relationship("Grant", back_populates="expenses")

    __table_args__ = (
        Index("ix_expense_date_category", "purchased_at", "category"),
        Index("ix_expense_grant", "grant_id", "purchased_at"),
    )

    def __repr__(self):
        return f"<Expense(id={self.id}, item='{self.item}', total={self.total_price})>"
