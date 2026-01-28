"""
Tools issued model for tracking equipment provided to students.
"""

from typing import Optional

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin


class ToolsIssued(TimestampMixin, SoftDeleteMixin, Base):
    """
    Tracks tools and equipment issued to students.

    Supports tracking issuance, returns, and condition.
    Soft delete preserves history of all tool transactions.
    """

    __tablename__ = "tools_issued"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Tool details
    tool_name = Column(String(255), nullable=False, index=True)
    tool_category = Column(
        String(100), nullable=True
    )  # e.g., "Hand Tools", "PPE", "Meters"
    serial_number = Column(String(100), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)

    # Issuance tracking
    date_issued = Column(Date, nullable=False, index=True)
    issued_by = Column(String(100), nullable=True)  # Staff name who issued

    # Return tracking
    date_returned = Column(Date, nullable=True)
    is_returned = Column(Boolean, default=False, nullable=False, index=True)
    return_condition = Column(String(50), nullable=True)  # good, damaged, lost

    # Value tracking (for inventory/loss reporting)
    unit_value = Column(Integer, nullable=True)  # Cost in cents

    notes = Column(Text, nullable=True)

    # Receipt/documentation
    receipt_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationship
    # OLD SYSTEM - student = relationship("Student", back_populates="tools_issued")

    __table_args__ = (
        Index("ix_tools_student_date", "student_id", "date_issued"),
        Index("ix_tools_outstanding", "is_returned", "student_id"),
    )

    def __repr__(self):
        status = "returned" if self.is_returned else "issued"
        return f"<ToolsIssued(id={self.id}, tool='{self.tool_name}', student={self.student_id}, {status})>"
