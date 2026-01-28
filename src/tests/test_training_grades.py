"""Tests for Training Grades endpoints."""

import uuid
from datetime import date


async def test_create_grade(async_client, db_session):
    """Test creating a new grade."""
    # Create complete setup: member, student, course
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

    payload = {
        "student_id": student.id,
        "course_id": course.id,
        "grade_type": "exam",
        "name": "Midterm Exam",
        "points_earned": 85.0,
        "points_possible": 100.0,
        "weight": 1.0,
        "grade_date": str(date.today()),
    }

    response = await async_client.post("/training/grades/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["student_id"] == student.id
    assert data["course_id"] == course.id
    assert data["points_earned"] == 85.0
    assert data["grade_type"] == "exam"


async def test_get_grade(async_client, db_session):
    """Test getting a grade by ID."""
    from src.models.member import Member
    from src.models.student import Student
    from src.models.course import Course
    from src.models.grade import Grade
    from src.db.enums import (
        MemberStatus,
        MemberClassification,
        StudentStatus,
        CourseType,
        GradeType,
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

    grade = Grade(
        student_id=student.id,
        course_id=course.id,
        grade_type=GradeType.QUIZ,
        name="Quiz 1",
        points_earned=90.0,
        points_possible=100.0,
        weight=1.0,
        grade_date=date.today(),
    )
    db_session.add(grade)
    db_session.commit()

    response = await async_client.get(f"/training/grades/{grade.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == grade.id
    assert data["name"] == "Quiz 1"


async def test_list_grades(async_client):
    """Test listing grades."""
    response = await async_client.get("/training/grades/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_update_grade(async_client, db_session):
    """Test updating a grade."""
    from src.models.member import Member
    from src.models.student import Student
    from src.models.course import Course
    from src.models.grade import Grade
    from src.db.enums import (
        MemberStatus,
        MemberClassification,
        StudentStatus,
        CourseType,
        GradeType,
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

    grade = Grade(
        student_id=student.id,
        course_id=course.id,
        grade_type=GradeType.ASSIGNMENT,
        name="Assignment 1",
        points_earned=75.0,
        points_possible=100.0,
        weight=1.0,
        grade_date=date.today(),
    )
    db_session.add(grade)
    db_session.commit()

    # Update it
    update_payload = {
        "points_earned": 85.0,
        "feedback": "Improved work!",
    }
    response = await async_client.patch(f"/training/grades/{grade.id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["points_earned"] == 85.0


async def test_delete_grade(async_client, db_session):
    """Test deleting a grade."""
    from src.models.member import Member
    from src.models.student import Student
    from src.models.course import Course
    from src.models.grade import Grade
    from src.db.enums import (
        MemberStatus,
        MemberClassification,
        StudentStatus,
        CourseType,
        GradeType,
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

    grade = Grade(
        student_id=student.id,
        course_id=course.id,
        grade_type=GradeType.EXAM,
        name="Final Exam",
        points_earned=92.0,
        points_possible=100.0,
        weight=1.0,
        grade_date=date.today(),
    )
    db_session.add(grade)
    db_session.commit()

    # Delete it
    response = await async_client.delete(f"/training/grades/{grade.id}")
    assert response.status_code == 200
