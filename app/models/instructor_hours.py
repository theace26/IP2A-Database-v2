from sqlalchemy import Column, Integer, Date, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class InstructorHours(Base):
    __tablename__ = "instructor_hours"

    id = Column(Integer, primary_key=True, index=True)

    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    cohort_id = Column(Integer, ForeignKey("cohorts.id"), nullable=True)

    date = Column(Date, nullable=False)
    hours = Column(Numeric(5, 2), nullable=False)
    prep_hours = Column(Numeric(5, 2), nullable=True)
    total_hours = Column(Numeric(6, 2), nullable=True)
    notes = Column(Text, nullable=True)

    instructor = relationship("Instructor", back_populates="hours_entries")
    location = relationship("Location", back_populates="instructor_hours")
    cohort = relationship("Cohort", back_populates="instructor_hours")
