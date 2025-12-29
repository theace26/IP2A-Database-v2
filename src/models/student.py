from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from src.db.base import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)

    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False, unique=True)

    # Increased from 20 to 50 to avoid truncation errors
    phone = Column(String(50), nullable=True)

    birthdate = Column(Date, nullable=True)
    address = Column(String(255), nullable=True)

    # Cohort assignment
    cohort_id = Column(Integer, ForeignKey("cohorts.id"), nullable=True)
    cohort = relationship("Cohort", back_populates="students")

    # Profile photo
    profile_photo_path = Column(String, nullable=True)

    # Added relationships for seeding
    tools_issued = relationship(
        "ToolsIssued", back_populates="student", cascade="all, delete-orphan"
    )
    credentials = relationship(
        "Credential", back_populates="student", cascade="all, delete-orphan"
    )
    jatc_applications = relationship(
        "JATCApplication", back_populates="student", cascade="all, delete-orphan"
    )
