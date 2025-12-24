from typing import Optional

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.db.base import Base




class ToolsIssued(Base):
    __tablename__ = "tools_issued"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)

    tool_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    # ✅ Missing field added
    date_issued = Column(Date, nullable=False)

    notes = Column(Text, nullable=True)

    student = relationship("Student", back_populates="tools_issued")

    receipt_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)

