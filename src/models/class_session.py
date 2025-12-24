from sqlalchemy import Column, Integer, Date, Time, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from src.db.base import Base


class ClassSession(Base):
    __tablename__ = "class_sessions"

    id = Column(Integer, primary_key=True, index=True)

    cohort_id = Column(Integer, ForeignKey("cohorts.id"), nullable=False)
    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)

    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)

    topic = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    cohort = relationship("Cohort", backref="class_sessions")
    instructor = relationship("Instructor", backref="class_sessions")
    location = relationship("Location", backref="class_sessions")
