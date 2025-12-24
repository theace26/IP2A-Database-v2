from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from src.db.base import Base


class JATCApplication(Base):
    __tablename__ = "jatc_applications"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)

    application_date = Column(Date, nullable=False)
    interview_date = Column(Date, nullable=True)  # ✅ CORRECT
    status = Column(String(255), nullable=False)

    notes = Column(Text, nullable=True)
    supporting_docs_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    student = relationship("Student", back_populates="jatc_applications")
