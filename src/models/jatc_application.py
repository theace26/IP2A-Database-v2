from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    Text,
    Index,
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

    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False,
        index=True,
    )

    application_date = Column(Date, nullable=False)
    interview_date = Column(Date, nullable=True)
    status = Column(String(255), nullable=False)

    notes = Column(Text, nullable=True)
    supporting_docs_path: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
    )

    student = relationship(
        "Student",
        back_populates="jatc_applications",
    )

    __table_args__ = (
        Index("ix_jatc_student_id", "student_id"),
        Index("ix_jatc_status", "status"),
        Index("ix_jatc_application_date", "application_date"),
        Index("ix_jatc_interview_date", "interview_date"),
    )
