# Claude Code Instructions: Phase 2 (Roadmap) - Pre-Apprenticeship System

> **Project:** IP2A-Database-v2
> **Phase:** 2 (Roadmap) - Pre-Apprenticeship Training System
> **Estimated Time:** 6-8 hours
> **Prerequisites:** Phase 1.3 complete (User registration working)

---

## Objective

Implement the core pre-apprenticeship training system - the original purpose of IP2A:
- Student records (linked to Members)
- Training programs and courses
- Class sessions with attendance
- Grades and assessments
- Certification tracking

---

## Before You Start

### 1. Verify Environment

```bash
cd ~/Projects/IP2A-Database-v2
git status                    # Should be clean, on main
git pull origin main          # Get latest
pytest -v                     # Verify all tests pass
```

### 2. Review Existing Patterns

```bash
cat src/models/member.py            # Member pattern
cat src/models/benevolence_application.py  # FK relationships
cat src/services/member_service.py  # Service pattern
cat src/routers/members.py          # Router pattern
cat src/db/enums/base_enums.py      # Enum patterns
```

---

## Data Model Overview

```
┌─────────────────┐     ┌─────────────────┐
│     Member      │────<│     Student     │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼─────┐ ┌────▼────┐ ┌────▼────────┐
              │Enrollment │ │  Grade  │ │Certification│
              └─────┬─────┘ └─────────┘ └─────────────┘
                    │
              ┌─────▼─────┐
              │  Course   │
              └─────┬─────┘
                    │
              ┌─────▼─────┐
              │ClassSession│
              └─────┬─────┘
                    │
              ┌─────▼─────┐
              │Attendance │
              └───────────┘
```

---

## Implementation Steps

### Step 1: Create Training Enums

**File:** `src/db/enums/training_enums.py`

```python
"""Enums for pre-apprenticeship training system."""

from enum import Enum


class StudentStatus(str, Enum):
    """Student enrollment status."""
    APPLICANT = "applicant"           # Applied, not yet accepted
    ENROLLED = "enrolled"             # Currently in program
    ON_LEAVE = "on_leave"             # Temporary leave
    COMPLETED = "completed"           # Finished program
    DROPPED = "dropped"               # Dropped out
    DISMISSED = "dismissed"           # Removed from program


class EnrollmentStatus(str, Enum):
    """Course enrollment status."""
    ENROLLED = "enrolled"             # Currently enrolled
    COMPLETED = "completed"           # Completed course
    WITHDRAWN = "withdrawn"           # Withdrew from course
    FAILED = "failed"                 # Did not pass
    INCOMPLETE = "incomplete"         # Did not finish


class AttendanceStatus(str, Enum):
    """Class session attendance status."""
    PRESENT = "present"
    ABSENT = "absent"
    EXCUSED = "excused"
    LATE = "late"
    LEFT_EARLY = "left_early"


class GradeType(str, Enum):
    """Type of grade/assessment."""
    ASSIGNMENT = "assignment"
    QUIZ = "quiz"
    EXAM = "exam"
    PROJECT = "project"
    PARTICIPATION = "participation"
    FINAL = "final"


class CertificationType(str, Enum):
    """Type of certification."""
    OSHA_10 = "osha_10"
    OSHA_30 = "osha_30"
    FIRST_AID = "first_aid"
    CPR = "cpr"
    FORKLIFT = "forklift"
    AERIAL_LIFT = "aerial_lift"
    CONFINED_SPACE = "confined_space"
    HAZMAT = "hazmat"
    FLAGGER = "flagger"
    ELECTRICAL_TRAINEE = "electrical_trainee"
    OTHER = "other"


class CertificationStatus(str, Enum):
    """Certification status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class CourseType(str, Enum):
    """Type of course."""
    CORE = "core"                     # Required for all students
    ELECTIVE = "elective"             # Optional course
    REMEDIAL = "remedial"             # For students needing extra help
    ADVANCED = "advanced"             # Advanced topics
    CERTIFICATION = "certification"   # Certification prep
```

**Update:** `src/db/enums/__init__.py` - Add exports:

```python
from src.db.enums.training_enums import (
    StudentStatus,
    EnrollmentStatus,
    AttendanceStatus,
    GradeType,
    CertificationType,
    CertificationStatus,
    CourseType,
)

__all__ = [
    # ... existing exports ...
    "StudentStatus",
    "EnrollmentStatus",
    "AttendanceStatus",
    "GradeType",
    "CertificationType",
    "CertificationStatus",
    "CourseType",
]
```

---

### Step 2: Create Student Model

**File:** `src/models/student.py`

```python
"""Student model for pre-apprenticeship program."""

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, Date, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import StudentStatus

if TYPE_CHECKING:
    from src.models.member import Member
    from src.models.enrollment import Enrollment
    from src.models.grade import Grade
    from src.models.certification import Certification
    from src.models.attendance import Attendance


class Student(Base, TimestampMixin, SoftDeleteMixin):
    """
    Student in the pre-apprenticeship program.
    
    A Student is linked to a Member record. Not all Members are Students,
    but all Students should have a Member record.
    """
    
    __tablename__ = "students"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Link to Member (required)
    member_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("members.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,  # One student record per member
        index=True
    )
    
    # Student-specific fields
    student_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )
    
    status: Mapped[StudentStatus] = mapped_column(
        SQLEnum(StudentStatus, name="student_status_enum"),
        default=StudentStatus.APPLICANT,
        nullable=False,
        index=True
    )
    
    # Program dates
    application_date: Mapped[date] = mapped_column(Date, nullable=False)
    enrollment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expected_completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Program info
    cohort: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "2026-Spring"
    
    # Emergency contact
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    emergency_contact_relationship: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    member: Mapped["Member"] = relationship(
        "Member",
        back_populates="student",
        lazy="joined"
    )
    
    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="student",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    grades: Mapped[list["Grade"]] = relationship(
        "Grade",
        back_populates="student",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    certifications: Mapped[list["Certification"]] = relationship(
        "Certification",
        back_populates="student",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    attendances: Mapped[list["Attendance"]] = relationship(
        "Attendance",
        back_populates="student",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    @property
    def full_name(self) -> str:
        """Get student's full name from member."""
        return f"{self.member.first_name} {self.member.last_name}"
    
    @property
    def is_active(self) -> bool:
        """Check if student is currently active in program."""
        return self.status in [StudentStatus.ENROLLED, StudentStatus.ON_LEAVE]
    
    def __repr__(self) -> str:
        return f"<Student(id={self.id}, number='{self.student_number}', status={self.status})>"
```

---

### Step 3: Create Course Model

**File:** `src/models/course.py`

```python
"""Course model for training program."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, Text, Boolean, Float, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.mixins import TimestampMixin, SoftDeleteMixin
from src.db.enums import CourseType

if TYPE_CHECKING:
    from src.models.class_session import ClassSession
    from src.models.enrollment import Enrollment
    from src.models.grade import Grade


class Course(Base, TimestampMixin, SoftDeleteMixin):
    """
    Course in the pre-apprenticeship curriculum.
    
    Courses are reusable templates. ClassSessions are specific
    instances of courses with dates and instructors.
    """
    
    __tablename__ = "courses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Course identification
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Course type
    course_type: Mapped[CourseType] = mapped_column(
        SQLEnum(CourseType, name="course_type_enum"),
        default=CourseType.CORE,
        nullable=False
    )
    
    # Requirements
    credits: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    hours: Mapped[int] = mapped_column(Integer, default=40, nullable=False)  # Total contact hours
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Grading
    passing_grade: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    
    # Prerequisites (comma-separated course codes)
    prerequisites: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Active status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    class_sessions: Mapped[list["ClassSession"]] = relationship(
        "ClassSession",
        back_populates="course",
        lazy="selectin"
    )
    
    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="course",
        lazy="selectin"
    )
    
    grades: Mapped[list["Grade"]] = relationship(
        "Grade",
        back_populates="course",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Course(id={self.id}, code='{self.code}', name='{self.name}')>"
```

---

### Step 4: Create ClassSession Model

**File:** `src/models/class_session.py`

```python
"""Class session model - specific instances of courses."""

from datetime import date, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, Date, Time, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.models.course import Course
    from src.models.attendance import Attendance


class ClassSession(Base, TimestampMixin):
    """
    A specific class session - one meeting of a course.
    
    Multiple ClassSessions make up a course offering.
    Attendance is tracked per ClassSession.
    """
    
    __tablename__ = "class_sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Link to course
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Session details
    session_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    
    # Location
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    room: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Instructor
    instructor_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Session info
    topic: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Relationships
    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="class_sessions",
        lazy="joined"
    )
    
    attendances: Mapped[list["Attendance"]] = relationship(
        "Attendance",
        back_populates="class_session",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    @property
    def duration_hours(self) -> float:
        """Calculate session duration in hours."""
        from datetime import datetime
        start = datetime.combine(self.session_date, self.start_time)
        end = datetime.combine(self.session_date, self.end_time)
        return (end - start).seconds / 3600
    
    def __repr__(self) -> str:
        return f"<ClassSession(id={self.id}, course_id={self.course_id}, date={self.session_date})>"
```

---

### Step 5: Create Enrollment Model

**File:** `src/models/enrollment.py`

```python
"""Enrollment model - student enrollment in courses."""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, Date, Float, Text, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.mixins import TimestampMixin
from src.db.enums import EnrollmentStatus

if TYPE_CHECKING:
    from src.models.student import Student
    from src.models.course import Course


class Enrollment(Base, TimestampMixin):
    """
    Student enrollment in a course.
    
    Tracks when a student enrolled, their status, and final grade.
    """
    
    __tablename__ = "enrollments"
    
    __table_args__ = (
        # Student can only enroll in a course once per cohort/term
        UniqueConstraint("student_id", "course_id", "cohort", name="uq_student_course_cohort"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Enrollment details
    cohort: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "2026-Spring"
    enrollment_date: Mapped[date] = mapped_column(Date, nullable=False)
    completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Status
    status: Mapped[EnrollmentStatus] = mapped_column(
        SQLEnum(EnrollmentStatus, name="enrollment_status_enum"),
        default=EnrollmentStatus.ENROLLED,
        nullable=False,
        index=True
    )
    
    # Final grade
    final_grade: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    letter_grade: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)  # A, B+, etc.
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="enrollments",
        lazy="joined"
    )
    
    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="enrollments",
        lazy="joined"
    )
    
    @property
    def is_passing(self) -> Optional[bool]:
        """Check if student is passing based on final grade."""
        if self.final_grade is None:
            return None
        return self.final_grade >= self.course.passing_grade
    
    def __repr__(self) -> str:
        return f"<Enrollment(id={self.id}, student_id={self.student_id}, course_id={self.course_id})>"
```

---

### Step 6: Create Attendance Model

**File:** `src/models/attendance.py`

```python
"""Attendance model for class sessions."""

from datetime import time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, Time, Text, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.mixins import TimestampMixin
from src.db.enums import AttendanceStatus

if TYPE_CHECKING:
    from src.models.student import Student
    from src.models.class_session import ClassSession


class Attendance(Base, TimestampMixin):
    """
    Attendance record for a student at a class session.
    """
    
    __tablename__ = "attendances"
    
    __table_args__ = (
        UniqueConstraint("student_id", "class_session_id", name="uq_student_session"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    class_session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("class_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Attendance status
    status: Mapped[AttendanceStatus] = mapped_column(
        SQLEnum(AttendanceStatus, name="attendance_status_enum"),
        nullable=False,
        index=True
    )
    
    # Time tracking (for late arrivals / early departures)
    arrival_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    departure_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="attendances",
        lazy="joined"
    )
    
    class_session: Mapped["ClassSession"] = relationship(
        "ClassSession",
        back_populates="attendances",
        lazy="joined"
    )
    
    def __repr__(self) -> str:
        return f"<Attendance(student_id={self.student_id}, session_id={self.class_session_id}, status={self.status})>"
```

---

### Step 7: Create Grade Model

**File:** `src/models/grade.py`

```python
"""Grade model for student assessments."""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, Date, Float, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.mixins import TimestampMixin
from src.db.enums import GradeType

if TYPE_CHECKING:
    from src.models.student import Student
    from src.models.course import Course


class Grade(Base, TimestampMixin):
    """
    Individual grade/assessment for a student in a course.
    
    Multiple grades per student per course are expected
    (assignments, quizzes, exams, etc.).
    """
    
    __tablename__ = "grades"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Grade details
    grade_type: Mapped[GradeType] = mapped_column(
        SQLEnum(GradeType, name="grade_type_enum"),
        nullable=False
    )
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)  # e.g., "Week 3 Quiz"
    
    # Scoring
    points_earned: Mapped[float] = mapped_column(Float, nullable=False)
    points_possible: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)  # For weighted grades
    
    # Date
    grade_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Feedback
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Who graded
    graded_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="grades",
        lazy="joined"
    )
    
    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="grades",
        lazy="joined"
    )
    
    @property
    def percentage(self) -> float:
        """Calculate percentage score."""
        if self.points_possible == 0:
            return 0.0
        return (self.points_earned / self.points_possible) * 100
    
    @property
    def letter_grade(self) -> str:
        """Convert percentage to letter grade."""
        pct = self.percentage
        if pct >= 90:
            return "A"
        elif pct >= 80:
            return "B"
        elif pct >= 70:
            return "C"
        elif pct >= 60:
            return "D"
        else:
            return "F"
    
    def __repr__(self) -> str:
        return f"<Grade(id={self.id}, student_id={self.student_id}, name='{self.name}')>"
```

---

### Step 8: Create Certification Model

**File:** `src/models/certification.py`

```python
"""Certification model for student certifications."""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, Date, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.mixins import TimestampMixin
from src.db.enums import CertificationType, CertificationStatus

if TYPE_CHECKING:
    from src.models.student import Student


class Certification(Base, TimestampMixin):
    """
    Certification earned by a student.
    
    Tracks OSHA, first aid, and other certifications
    required or earned during the program.
    """
    
    __tablename__ = "certifications"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Certification type
    cert_type: Mapped[CertificationType] = mapped_column(
        SQLEnum(CertificationType, name="certification_type_enum"),
        nullable=False,
        index=True
    )
    
    # For custom certifications
    custom_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Status
    status: Mapped[CertificationStatus] = mapped_column(
        SQLEnum(CertificationStatus, name="certification_status_enum"),
        default=CertificationStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Dates
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Certificate details
    certificate_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    issuing_organization: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Verification
    verified_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    verification_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="certifications",
        lazy="joined"
    )
    
    @property
    def display_name(self) -> str:
        """Get display name for certification."""
        if self.cert_type == CertificationType.OTHER and self.custom_name:
            return self.custom_name
        return self.cert_type.value.replace("_", " ").title()
    
    @property
    def is_expired(self) -> bool:
        """Check if certification has expired."""
        if not self.expiration_date:
            return False
        return date.today() > self.expiration_date
    
    @property
    def is_valid(self) -> bool:
        """Check if certification is currently valid."""
        return self.status == CertificationStatus.ACTIVE and not self.is_expired
    
    def __repr__(self) -> str:
        return f"<Certification(id={self.id}, student_id={self.student_id}, type={self.cert_type})>"
```

---

### Step 9: Update Member Model

**File:** `src/models/member.py` - Add student relationship

Add to TYPE_CHECKING imports:
```python
if TYPE_CHECKING:
    # ... existing imports ...
    from src.models.student import Student
```

Add relationship:
```python
    student: Mapped[Optional["Student"]] = relationship(
        "Student",
        back_populates="member",
        uselist=False,
        lazy="joined"
    )
```

---

### Step 10: Update Models __init__.py

**File:** `src/models/__init__.py`

```python
# Training models
from src.models.student import Student
from src.models.course import Course
from src.models.class_session import ClassSession
from src.models.enrollment import Enrollment
from src.models.attendance import Attendance
from src.models.grade import Grade
from src.models.certification import Certification

__all__ = [
    # ... existing exports ...
    # Training
    "Student",
    "Course",
    "ClassSession",
    "Enrollment",
    "Attendance",
    "Grade",
    "Certification",
]
```

---

### Step 11: Create Database Migration

```bash
alembic revision --autogenerate -m "Add pre-apprenticeship training models"
alembic upgrade head
```

---

### Step 12: Create Schemas

**File:** `src/schemas/student.py`

```python
"""Pydantic schemas for Student model."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.db.enums import StudentStatus


class StudentBase(BaseModel):
    """Base schema for Student."""
    
    student_number: str = Field(..., min_length=1, max_length=20)
    status: StudentStatus = StudentStatus.APPLICANT
    application_date: date
    enrollment_date: Optional[date] = None
    expected_completion_date: Optional[date] = None
    cohort: Optional[str] = Field(None, max_length=50)
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class StudentCreate(StudentBase):
    """Schema for creating a Student."""
    
    member_id: int


class StudentUpdate(BaseModel):
    """Schema for updating a Student."""
    
    status: Optional[StudentStatus] = None
    enrollment_date: Optional[date] = None
    expected_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    cohort: Optional[str] = Field(None, max_length=50)
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class StudentRead(StudentBase):
    """Schema for reading a Student."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    member_id: int
    actual_completion_date: Optional[date] = None
    created_at: date
    updated_at: date
    
    # From member relationship
    full_name: str


class StudentReadWithDetails(StudentRead):
    """Schema for reading Student with enrollment details."""
    
    enrollment_count: int = 0
    certification_count: int = 0
    attendance_rate: Optional[float] = None
```

Create similar schemas for:
- `src/schemas/course.py`
- `src/schemas/class_session.py`
- `src/schemas/enrollment.py`
- `src/schemas/attendance.py`
- `src/schemas/grade.py`
- `src/schemas/certification.py`

---

### Step 13: Create Services

**File:** `src/services/student_service.py`

```python
"""Service functions for Student model."""

from datetime import date
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.models.student import Student
from src.models.member import Member
from src.db.enums import StudentStatus
from src.schemas.student import StudentCreate, StudentUpdate


def generate_student_number(db: Session, year: int = None) -> str:
    """Generate a unique student number (YYYY-NNNN format)."""
    if year is None:
        year = date.today().year
    
    # Find the highest number for this year
    prefix = f"{year}-"
    result = db.execute(
        select(Student.student_number)
        .where(Student.student_number.like(f"{prefix}%"))
        .order_by(Student.student_number.desc())
        .limit(1)
    ).scalar_one_or_none()
    
    if result:
        last_num = int(result.split("-")[1])
        next_num = last_num + 1
    else:
        next_num = 1
    
    return f"{year}-{next_num:04d}"


def get_student(db: Session, student_id: int) -> Optional[Student]:
    """Get a student by ID."""
    return db.get(Student, student_id)


def get_student_by_number(db: Session, student_number: str) -> Optional[Student]:
    """Get a student by student number."""
    stmt = select(Student).where(Student.student_number == student_number)
    return db.execute(stmt).scalar_one_or_none()


def get_student_by_member(db: Session, member_id: int) -> Optional[Student]:
    """Get student record for a member."""
    stmt = select(Student).where(Student.member_id == member_id)
    return db.execute(stmt).scalar_one_or_none()


def get_students(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[StudentStatus] = None,
    cohort: Optional[str] = None,
) -> list[Student]:
    """Get list of students with optional filters."""
    stmt = select(Student)
    
    if status:
        stmt = stmt.where(Student.status == status)
    if cohort:
        stmt = stmt.where(Student.cohort == cohort)
    
    stmt = stmt.offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def create_student(db: Session, student_data: StudentCreate) -> Student:
    """Create a new student."""
    student = Student(
        member_id=student_data.member_id,
        student_number=student_data.student_number,
        status=student_data.status,
        application_date=student_data.application_date,
        enrollment_date=student_data.enrollment_date,
        expected_completion_date=student_data.expected_completion_date,
        cohort=student_data.cohort,
        emergency_contact_name=student_data.emergency_contact_name,
        emergency_contact_phone=student_data.emergency_contact_phone,
        emergency_contact_relationship=student_data.emergency_contact_relationship,
        notes=student_data.notes,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def update_student(db: Session, student: Student, student_data: StudentUpdate) -> Student:
    """Update an existing student."""
    update_data = student_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


def delete_student(db: Session, student: Student) -> None:
    """Soft delete a student."""
    student.soft_delete()
    db.commit()


def get_student_attendance_rate(db: Session, student_id: int) -> Optional[float]:
    """Calculate attendance rate for a student."""
    from src.models.attendance import Attendance
    from src.db.enums import AttendanceStatus
    
    total = db.execute(
        select(func.count(Attendance.id))
        .where(Attendance.student_id == student_id)
    ).scalar()
    
    if not total:
        return None
    
    present = db.execute(
        select(func.count(Attendance.id))
        .where(
            Attendance.student_id == student_id,
            Attendance.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.LATE])
        )
    ).scalar()
    
    return (present / total) * 100 if total > 0 else 0.0
```

Create similar services for:
- `src/services/course_service.py`
- `src/services/class_session_service.py`
- `src/services/enrollment_service.py`
- `src/services/attendance_service.py`
- `src/services/grade_service.py`
- `src/services/certification_service.py`

---

### Step 14: Create Routers

**File:** `src/routers/students.py`

```python
"""Router for student endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.db.enums import StudentStatus
from src.schemas.student import StudentCreate, StudentUpdate, StudentRead, StudentReadWithDetails
from src.services import student_service
from src.routers.dependencies.auth import CurrentUser, StaffUser

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/", response_model=list[StudentRead])
def list_students(
    user: CurrentUser,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[StudentStatus] = None,
    cohort: Optional[str] = None,
):
    """List students with optional filters."""
    return student_service.get_students(db, skip, limit, status, cohort)


@router.get("/{student_id}", response_model=StudentReadWithDetails)
def get_student(
    student_id: int,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    """Get a student by ID."""
    student = student_service.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Add computed fields
    attendance_rate = student_service.get_student_attendance_rate(db, student_id)
    
    return StudentReadWithDetails(
        **StudentRead.model_validate(student).model_dump(),
        enrollment_count=len(student.enrollments),
        certification_count=len(student.certifications),
        attendance_rate=attendance_rate,
    )


@router.post("/", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(
    student_data: StudentCreate,
    user: StaffUser,
    db: Session = Depends(get_db),
):
    """Create a new student (staff only)."""
    # Check member exists
    from src.services.member_service import get_member
    member = get_member(db, student_data.member_id)
    if not member:
        raise HTTPException(status_code=400, detail="Member not found")
    
    # Check not already a student
    existing = student_service.get_student_by_member(db, student_data.member_id)
    if existing:
        raise HTTPException(status_code=409, detail="Member is already a student")
    
    return student_service.create_student(db, student_data)


@router.patch("/{student_id}", response_model=StudentRead)
def update_student(
    student_id: int,
    student_data: StudentUpdate,
    user: StaffUser,
    db: Session = Depends(get_db),
):
    """Update a student (staff only)."""
    student = student_service.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return student_service.update_student(db, student, student_data)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    user: StaffUser,
    db: Session = Depends(get_db),
):
    """Delete a student (staff only, soft delete)."""
    student = student_service.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student_service.delete_student(db, student)
    return None
```

Create similar routers for:
- `src/routers/courses.py`
- `src/routers/class_sessions.py`
- `src/routers/enrollments.py`
- `src/routers/attendances.py`
- `src/routers/grades.py`
- `src/routers/certifications.py`

---

### Step 15: Register Routers in main.py

```python
from src.routers.students import router as students_router
from src.routers.courses import router as courses_router
# ... etc

app.include_router(students_router)
app.include_router(courses_router)
# ... etc
```

---

### Step 16: Create Seed Data

**File:** `src/seed/training_seed.py`

```python
"""Seed data for pre-apprenticeship training system."""

from datetime import date, time, timedelta
import random

from sqlalchemy.orm import Session

from src.models.student import Student
from src.models.course import Course
from src.models.class_session import ClassSession
from src.models.enrollment import Enrollment
from src.models.attendance import Attendance
from src.models.grade import Grade
from src.models.certification import Certification
from src.db.enums import (
    StudentStatus,
    EnrollmentStatus,
    AttendanceStatus,
    GradeType,
    CertificationType,
    CertificationStatus,
    CourseType,
)


def seed_courses(db: Session) -> list[Course]:
    """Seed default courses."""
    courses = [
        Course(
            code="ELEC-101",
            name="Electrical Fundamentals",
            description="Introduction to electrical theory, safety, and basic circuits.",
            course_type=CourseType.CORE,
            credits=3.0,
            hours=80,
            is_required=True,
            passing_grade=70.0,
        ),
        Course(
            code="MATH-100",
            name="Construction Math",
            description="Applied mathematics for construction trades.",
            course_type=CourseType.CORE,
            credits=2.0,
            hours=40,
            is_required=True,
            passing_grade=70.0,
        ),
        Course(
            code="SAFE-101",
            name="Construction Safety",
            description="OSHA 10 certification preparation and general safety.",
            course_type=CourseType.CERTIFICATION,
            credits=1.0,
            hours=16,
            is_required=True,
            passing_grade=80.0,
        ),
        Course(
            code="TOOL-101",
            name="Hand and Power Tools",
            description="Proper use and maintenance of construction tools.",
            course_type=CourseType.CORE,
            credits=2.0,
            hours=40,
            is_required=True,
            passing_grade=70.0,
        ),
        Course(
            code="READ-101",
            name="Blueprint Reading",
            description="Reading and interpreting construction drawings.",
            course_type=CourseType.CORE,
            credits=2.0,
            hours=40,
            is_required=True,
            passing_grade=70.0,
        ),
    ]
    
    for course in courses:
        existing = db.query(Course).filter(Course.code == course.code).first()
        if not existing:
            db.add(course)
    
    db.commit()
    return db.query(Course).all()


def seed_students(db: Session, count: int = 20) -> list[Student]:
    """Seed student records (requires existing members)."""
    from src.models.member import Member
    
    # Get members without student records
    members = db.query(Member).outerjoin(Student).filter(Student.id.is_(None)).limit(count).all()
    
    students = []
    cohorts = ["2025-Fall", "2026-Spring"]
    
    for i, member in enumerate(members):
        student = Student(
            member_id=member.id,
            student_number=f"2026-{i+1:04d}",
            status=random.choice(list(StudentStatus)),
            application_date=date.today() - timedelta(days=random.randint(30, 180)),
            cohort=random.choice(cohorts),
        )
        
        if student.status in [StudentStatus.ENROLLED, StudentStatus.COMPLETED]:
            student.enrollment_date = student.application_date + timedelta(days=random.randint(7, 30))
        
        db.add(student)
        students.append(student)
    
    db.commit()
    return students


def run_training_seed(db: Session) -> dict:
    """Run all training seed operations."""
    print("\n=== Seeding Training Data ===")
    
    courses = seed_courses(db)
    print(f"  Courses: {len(courses)}")
    
    students = seed_students(db)
    print(f"  Students: {len(students)}")
    
    return {
        "courses": len(courses),
        "students": len(students),
    }
```

---

### Step 17: Create Tests

Create test files:
- `src/tests/test_students.py`
- `src/tests/test_courses.py`
- `src/tests/test_enrollments.py`
- `src/tests/test_attendance.py`
- `src/tests/test_grades.py`
- `src/tests/test_certifications.py`

---

### Step 18: Run Tests and Verify

```bash
pytest -v
ruff check . --fix
ruff format .
```

---

## Verification Checklist

- [ ] 7 new models created (Student, Course, ClassSession, Enrollment, Attendance, Grade, Certification)
- [ ] Training enums created and exported
- [ ] Member model updated with student relationship
- [ ] Migration generated and applied
- [ ] Schemas for all models
- [ ] Services for all models
- [ ] Routers for all models
- [ ] Routers registered in main.py
- [ ] Seed data created
- [ ] Tests pass
- [ ] CLAUDE.md updated
- [ ] CHANGELOG.md updated

---

## Commit Message Template

```
feat(training): Add pre-apprenticeship training system

- Add Student model linked to Member
- Add Course model with types and requirements
- Add ClassSession for course instances
- Add Enrollment for student-course relationships
- Add Attendance tracking per session
- Add Grade model for assessments
- Add Certification tracking
- Add training enums (7 new enum types)
- Add schemas, services, routers for all models
- Add training seed data
- Add X new tests (Y total passing)

Phase 2 (Roadmap) complete. Core IP2A functionality implemented.
```

---

## API Endpoints Summary

| Resource | Endpoints | Auth |
|----------|-----------|------|
| `/students` | CRUD + filters | Staff+ |
| `/courses` | CRUD | Staff+ |
| `/class-sessions` | CRUD by course | Staff+ |
| `/enrollments` | CRUD by student/course | Staff+ |
| `/attendances` | CRUD by session | Staff+ |
| `/grades` | CRUD by student/course | Staff+ |
| `/certifications` | CRUD by student | Staff+ |

---

*End of Instructions*
