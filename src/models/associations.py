"""
Association tables for many-to-many relationships in the IP2A Database.
"""

from sqlalchemy import Table, Column, Integer, ForeignKey
from src.db.base import Base

# Many-to-many: Instructors <-> Cohorts
instructor_cohort = Table(
    "instructor_cohort",
    Base.metadata,
    Column(
        "instructor_id",
        Integer,
        ForeignKey("instructors.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "cohort_id",
        Integer,
        ForeignKey("cohorts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
