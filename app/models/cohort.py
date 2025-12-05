from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.associations import instructor_cohort


class Cohort(Base):
    __tablename__ = "cohorts"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    # Optional: primary / lead instructor for this cohort (for reporting/UI)
    primary_instructor_id = Column(
        Integer,
        ForeignKey("instructors.id"),
        nullable=True,
    )

    # Use foreign_keys to disambiguate from the many-to-many relationship
    primary_instructor = relationship(
        "Instructor",
        foreign_keys=[primary_instructor_id],
    )

    # Many-to-many: all instructors who have taught / are teaching this cohort
    instructors = relationship(
        "Instructor",
        secondary=instructor_cohort,
        back_populates="cohorts",
    )

    # Location assignment
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    location = relationship("Location", back_populates="cohorts")

    # Students in this cohort
    students = relationship("Student", back_populates="cohort")

    # Instructor hours logged against this cohort
    instructor_hours = relationship("InstructorHours", back_populates="cohort")
