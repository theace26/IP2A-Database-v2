from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.models.associations import instructor_cohort


class Instructor(Base):
    __tablename__ = "instructors"

    id = Column(Integer, primary_key=True, index=True)

    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False, unique=True)

    phone = Column(String(50), nullable=True)
    bio = Column(Text, nullable=True)
    certification = Column(String(255), nullable=True)

    # Many-to-many instructors <-> cohorts
    cohorts = relationship(
        "Cohort",
        secondary=instructor_cohort,
        back_populates="instructors",
    )

    # One-to-many: each Instructor has many logged hour entries
    hours_entries = relationship(
        "InstructorHours",
        back_populates="instructor",
        cascade="all, delete-orphan",
    )
