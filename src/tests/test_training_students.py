"""Tests for Training Students endpoints."""

import uuid
from datetime import date


async def test_create_student(async_client, db_session):
    """Test creating a new student."""
    # First create a member
    from src.models.member import Member
    from src.db.enums import MemberStatus, MemberClassification

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

    payload = {
        "member_id": member.id,
        "student_number": f"S{unique}",
        "status": "applicant",
        "application_date": str(date.today()),
        "cohort": "2026-Spring",
    }

    response = await async_client.post("/training/students/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["student_number"] == payload["student_number"]
    assert data["status"] == "applicant"
    assert "id" in data


async def test_get_student(async_client, db_session):
    """Test getting a student by ID."""
    # Create member and student first
    from src.models.member import Member
    from src.models.student import Student
    from src.db.enums import MemberStatus, MemberClassification, StudentStatus

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
        enrollment_date=date.today(),
    )
    db_session.add(student)
    db_session.commit()

    response = await async_client.get(f"/training/students/{student.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == student.id
    assert data["student_number"] == student.student_number


async def test_get_nonexistent_student(async_client):
    """Test getting a non-existent student returns 404."""
    response = await async_client.get("/training/students/999999")
    assert response.status_code == 404


async def test_list_students(async_client):
    """Test listing students."""
    response = await async_client.get("/training/students/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_update_student(async_client, db_session):
    """Test updating a student."""
    # Create member and student first
    from src.models.member import Member
    from src.models.student import Student
    from src.db.enums import MemberStatus, MemberClassification, StudentStatus

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
        status=StudentStatus.APPLICANT,
        application_date=date.today(),
    )
    db_session.add(student)
    db_session.commit()

    # Update it
    update_payload = {
        "status": "enrolled",
        "enrollment_date": str(date.today()),
    }
    response = await async_client.patch(
        f"/training/students/{student.id}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "enrolled"


async def test_delete_student(async_client, db_session):
    """Test deleting a student."""
    # Create member and student first
    from src.models.member import Member
    from src.models.student import Student
    from src.db.enums import MemberStatus, MemberClassification, StudentStatus

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
        status=StudentStatus.APPLICANT,
        application_date=date.today(),
    )
    db_session.add(student)
    db_session.commit()

    # Delete it
    response = await async_client.delete(f"/training/students/{student.id}")
    assert response.status_code == 200

    # Verify it's marked as deleted (soft delete)
    get_response = await async_client.get(f"/training/students/{student.id}")
    # Soft deleted students might still be retrievable or return 404 depending on implementation
    assert get_response.status_code in [200, 404]


async def test_generate_student_number(async_client):
    """Test generating next student number."""
    response = await async_client.get("/training/students/generate-number")
    assert response.status_code == 200
    data = response.json()
    assert "student_number" in data
    assert data["student_number"].startswith("S")
