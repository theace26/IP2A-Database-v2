from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class Credential(Base):
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)

    credential_name = Column(String(255), nullable=False)
    issuing_org = Column(String(255), nullable=True)

    issue_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=True)

    certificate_number = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # FIXED: use back_populates instead of backref
    student = relationship("Student", back_populates="credentials")
