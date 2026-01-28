"""Tests for Training Enrollments endpoints."""

import uuid
from datetime import date


async def test_create_enrollment(async_client, db_session):
    """Test creating a new enrollment."""
    # Create member, student, and course first
    from src.models.member import Member
    from src.models.student import Student
    from src.models.course import Course
    from src.db.enums import (
        MemberStatus,
        MemberClassification,
        StudentStatus,
        CourseType,
    )

    unique = str(uuid.uuid4())[:8]

    # Create member
    member = Member(
        member_number=f"M{unique}",
        first_name="Test",
        last_name="Student",
        status=MemberStatus.ACTIVE,
        classification=MemberClassification.APPRENTICE_1ST_YEAR,
    )
    db_session.add(member)
    db_session.commit()

    # Create student
    student = Student(
        member_id=member.id,
        student_number=f"S{unique}",
        status=StudentStatus.ENROLLED,
        application_date=date.today(),
        enrollment_date=date.today(),
    )
    db_session.add(student)
    db_session.commit()

    # Create course
    course = Course(
        code=f"TEST{unique[:4]}",
        name="Test Course",
        course_type=CourseType.CORE,
        credits=3.0,
        hours=60,
    )
    db_session.add(course)
    db_session.commit()

    payload = {
        "student_id": student.id,
        "course_id": course.id,
        "cohort": "2026-Spring",
        "enrollment_date": str(date.today()),
        "status": "enrolled",
    }

    response = await async_client.post("/training/enrollments/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["student_id"] == student.id
    assert data["course_id"] == course.id
    assert data["status"] == "enrolled"


async def test_get_enrollment(async_client, db_session):
    """Test getting an enrollment by ID."""
    # Create enrollment first
    from src.models.member import Member
    from src.models.student import Student
    from src.models.course import Course
    from src.models.enrollment import Enrollment
    from src.db.enums import (
        MemberStatus,
        MemberClassification,
        StudentStatus,
        CourseType,
        CourseEnrollmentStatus,
    )

    unique = str(uuid.uuid4())[:8]

    member = Member(
        member_number=f"M{unique}",
        first_name="Test",
        last_name="Student",
        status=MemberStatus.ACTIVE,
        classification=MemberClassification.APPRENTICE_1ST_YEAR,
    )
    db_session.add(member)
    db_session.commit()

    student = Student(
        member_id=member.id,
        student_number=f"S{unique}",
        status=StudentStatus.ENROLLED,
        application_date=date.today(),
    )
    db_session.add(student)
    db_session.commit()

    course = Course(
        code=f"TEST{unique[:4]}",
        name="Test Course",
        course_type=CourseType.CORE,
        credits=3.0,
        hours=60,
    )
    db_session.add(course)
    db_session.commit()

    enrollment = Enrollment(
        student_id=student.id,
        course_id=course.id,
        cohort="2026-Spring",
        enrollment_date=date.today(),
        status=CourseEnrollmentStatus.ENROLLED,
    )
    db_session.add(enrollment)
    db_session.commit()

    response = await async_client.get(f"/training/enrollments/{enrollment.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == enrollment.id


async def test_list_enrollments(async_client):
    """Test listing enrollments."""
    response = await async_client.get("/training/enrollments/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_update_enrollment(async_client, db_session):
    """Test updating an enrollment."""
    # Create enrollment first
    from src.models.member import Member
    from src.models.student import Student
    from src.models.course import Course
    from src.models.enrollment import Enrollment
    from src.db.enums import (
        MemberStatus,
        MemberClassification,
        StudentStatus,
        CourseType,
        CourseEnrollmentStatus,
    )

    unique = str(uuid.uuid4())[:8]

    member = Member(
        member_number=f"M{unique}",
        first_name="Test",
        last_name="Student",
        status=MemberStatus.ACTIVE,
        classification=MemberClassification.APPRENTICE_1ST_YEAR,
    )
    db_session.add(member)
    db_session.commit()

    student = Student(
        member_id=member.id,
        student_number=f"S{unique}",
        status=StudentStatus.ENROLLED,
        application_date=date.today(),
    )
    db_session.add(student)
    db_session.commit()

    course = Course(
        code=f"TEST{unique[:4]}",
        name="Test Course",
        course_type=CourseType.CORE,
        credits=3.0,
        hours=60,
    )
    db_session.add(course)
    db_session.commit()

    enrollment = Enrollment(
        student_id=student.id,
        course_id=course.id,
        cohort="2026-Spring",
        enrollment_date=date.today(),
        status=CourseEnrollmentStatus.ENROLLED,
    )
    db_session.add(enrollment)
    db_session.commit()

    # Update it
    update_payload = {
        "status": "completed",
        "final_grade": 85.5,
    }
    response = await async_client.patch(
        f"/training/enrollments/{enrollment.id}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["final_grade"] == 85.5


async def test_delete_enrollment(async_client, db_session):
    """Test deleting an enrollment."""
    # Create enrollment first
    from src.models.member import Member
    from src.models.student import Student
    from src.models.course import Course
    from src.models.enrollment import Enrollment
    from src.db.enums import (
        MemberStatus,
        MemberClassification,
        StudentStatus,
        CourseType,
        CourseEnrollmentStatus,
    )

    unique = str(uuid.uuid4())[:8]

    member = Member(
        member_number=f"M{unique}",
        first_name="Test",
        last_name="Student",
        status=MemberStatus.ACTIVE,
        classification=MemberClassification.APPRENTICE_1ST_YEAR,
    )
    db_session.add(member)
    db_session.commit()

    student = Student(
        member_id=member.id,
        student_number=f"S{unique}",
        status=StudentStatus.ENROLLED,
        application_date=date.today(),
    )
    db_session.add(student)
    db_session.commit()

    course = Course(
        code=f"TEST{unique[:4]}",
        name="Test Course",
        course_type=CourseType.CORE,
        credits=3.0,
        hours=60,
    )
    db_session.add(course)
    db_session.commit()

    enrollment = Enrollment(
        student_id=student.id,
        course_id=course.id,
        cohort="2026-Spring",
        enrollment_date=date.today(),
        status=CourseEnrollmentStatus.ENROLLED,
    )
    db_session.add(enrollment)
    db_session.commit()

    # Delete it
    response = await async_client.delete(f"/training/enrollments/{enrollment.id}")
    assert response.status_code == 200
