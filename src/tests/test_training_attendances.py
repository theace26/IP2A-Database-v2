"""Tests for Training Attendances endpoints."""

import uuid
from datetime import date, time


async def test_create_attendance(async_client, db_session):
    """Test creating a new attendance record."""
    # Create complete setup: member, student, course, class session
    from src.models.member import Member
    from src.models.student import Student
    from src.models.course import Course
    from src.models.class_session import ClassSession
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

    class_session = ClassSession(
        course_id=course.id,
        session_date=date.today(),
        start_time=time(18, 0),
        end_time=time(21, 0),
    )
    db_session.add(class_session)
    db_session.commit()

    payload = {
        "student_id": student.id,
        "class_session_id": class_session.id,
        "status": "present",
    }

    response = await async_client.post("/training/attendances/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["student_id"] == student.id
    assert data["class_session_id"] == class_session.id
    assert data["status"] == "present"


async def test_get_attendance(async_client, db_session):
    """Test getting an attendance record by ID."""
    from src.models.member import Member
    from src.models.student import Student
    from src.models.course import Course
    from src.models.class_session import ClassSession
    from src.models.attendance import Attendance
    from src.db.enums import (
        MemberStatus,
        MemberClassification,
        StudentStatus,
        CourseType,
        SessionAttendanceStatus,
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

    class_session = ClassSession(
        course_id=course.id,
        session_date=date.today(),
        start_time=time(18, 0),
        end_time=time(21, 0),
    )
    db_session.add(class_session)
    db_session.commit()

    attendance = Attendance(
        student_id=student.id,
        class_session_id=class_session.id,
        status=SessionAttendanceStatus.PRESENT,
    )
    db_session.add(attendance)
    db_session.commit()

    response = await async_client.get(f"/training/attendances/{attendance.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == attendance.id
    assert data["status"] == "present"


async def test_list_attendances(async_client):
    """Test listing attendance records."""
    response = await async_client.get("/training/attendances/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_update_attendance(async_client, db_session):
    """Test updating an attendance record."""
    from src.models.member import Member
    from src.models.student import Student
    from src.models.course import Course
    from src.models.class_session import ClassSession
    from src.models.attendance import Attendance
    from src.db.enums import (
        MemberStatus,
        MemberClassification,
        StudentStatus,
        CourseType,
        SessionAttendanceStatus,
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

    class_session = ClassSession(
        course_id=course.id,
        session_date=date.today(),
        start_time=time(18, 0),
        end_time=time(21, 0),
    )
    db_session.add(class_session)
    db_session.commit()

    attendance = Attendance(
        student_id=student.id,
        class_session_id=class_session.id,
        status=SessionAttendanceStatus.PRESENT,
    )
    db_session.add(attendance)
    db_session.commit()

    # Update it
    update_payload = {
        "status": "late",
        "arrival_time": "18:15:00",
    }
    response = await async_client.patch(
        f"/training/attendances/{attendance.id}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "late"


async def test_delete_attendance(async_client, db_session):
    """Test deleting an attendance record."""
    from src.models.member import Member
    from src.models.student import Student
    from src.models.course import Course
    from src.models.class_session import ClassSession
    from src.models.attendance import Attendance
    from src.db.enums import (
        MemberStatus,
        MemberClassification,
        StudentStatus,
        CourseType,
        SessionAttendanceStatus,
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

    class_session = ClassSession(
        course_id=course.id,
        session_date=date.today(),
        start_time=time(18, 0),
        end_time=time(21, 0),
    )
    db_session.add(class_session)
    db_session.commit()

    attendance = Attendance(
        student_id=student.id,
        class_session_id=class_session.id,
        status=SessionAttendanceStatus.PRESENT,
    )
    db_session.add(attendance)
    db_session.commit()

    # Delete it
    response = await async_client.delete(f"/training/attendances/{attendance.id}")
    assert response.status_code == 200
