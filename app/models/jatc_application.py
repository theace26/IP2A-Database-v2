from sqlalchemy import Column, Integer, Date, String, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from app.db.base import Base

class JATCApplication(Base):
    __tablename__ = "jatc_applications"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)

    application_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False)  # e.g., pending, accepted, denied, interviewed
    interview_date = Column(Date, nullable=True)

    score = Column(Numeric(5, 2), nullable=True)  # Optional interview score
    notes = Column(Text, nullable=True)

    # FIXED: convert backref → back_populates
    student = relationship("Student", back_populates="jatc_applications")
