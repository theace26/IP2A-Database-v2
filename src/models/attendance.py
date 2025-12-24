from sqlalchemy import (
    Column, Integer, String, ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from src.db.base import Base


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    class_session_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=False)

    # present / absent / tardy
    status = Column(String(20), nullable=False)

    # only relevant if tardy
    minutes_late = Column(Integer, nullable=True)

    notes = Column(Text, nullable=True)

    # Prevent duplicate attendance entries for the same session
    __table_args__ = (
        UniqueConstraint("student_id", "class_session_id", name="uq_student_session"),
    )

    student = relationship("Student", backref="attendance_records")
    class_session = relationship("ClassSession", backref="attendance_records")
