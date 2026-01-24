from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.db.base import Base


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    capacity = Column(Integer, nullable=True)

    # Relationships
    cohorts = relationship("Cohort", back_populates="location")
    instructor_hours = relationship(
        "InstructorHours", back_populates="location", cascade="all, delete"
    )
