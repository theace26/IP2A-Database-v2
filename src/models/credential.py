from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    Text,             # <-- REQUIRED FIX
)
from sqlalchemy.orm import (
    relationship,
    Mapped,
    mapped_column,
)

from src.db.base import Base


class Credential(Base):
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)

    credential_name = Column(String(255), nullable=False)
    issuing_org = Column(String(255), nullable=True)

    issue_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=True)

    certificate_number = Column(String(255), nullable=True)

    notes = Column(Text, nullable=True)   # <-- FIXED import required

    attachment_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    student = relationship("Student", back_populates="credentials")
