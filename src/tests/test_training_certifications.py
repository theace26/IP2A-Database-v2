"""Tests for Training Certifications endpoints."""

import uuid
from datetime import date, timedelta


async def test_create_certification(async_client, db_session):
    """Test creating a new certification."""
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
    )
    db_session.add(student)
    db_session.commit()

    payload = {
        "student_id": student.id,
        "cert_type": "osha_10",
        "status": "active",
        "issue_date": str(date.today()),
        "expiration_date": str(date.today() + timedelta(days=365)),
        "certificate_number": "OSHA10-12345",
        "issuing_organization": "OSHA",
    }

    response = await async_client.post("/training/certifications/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["student_id"] == student.id
    assert data["cert_type"] == "osha_10"
    assert data["status"] == "active"


async def test_get_certification(async_client, db_session):
    """Test getting a certification by ID."""
    from src.models.member import Member
    from src.models.student import Student
    from src.models.certification import Certification
    from src.db.enums import (
        MemberStatus,
        MemberClassification,
        StudentStatus,
        CertificationType,
        CertificationStatus,
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

    certification = Certification(
        student_id=student.id,
        cert_type=CertificationType.FIRST_AID,
        status=CertificationStatus.ACTIVE,
        issue_date=date.today(),
        certificate_number="FA-12345",
    )
    db_session.add(certification)
    db_session.commit()

    response = await async_client.get(f"/training/certifications/{certification.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == certification.id
    assert data["cert_type"] == "first_aid"


async def test_list_certifications(async_client):
    """Test listing certifications."""
    response = await async_client.get("/training/certifications/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_update_certification(async_client, db_session):
    """Test updating a certification."""
    from src.models.member import Member
    from src.models.student import Student
    from src.models.certification import Certification
    from src.db.enums import (
        MemberStatus,
        MemberClassification,
        StudentStatus,
        CertificationType,
        CertificationStatus,
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

    certification = Certification(
        student_id=student.id,
        cert_type=CertificationType.CPR,
        status=CertificationStatus.PENDING,
        issue_date=None,
    )
    db_session.add(certification)
    db_session.commit()

    # Update it
    update_payload = {
        "status": "active",
        "issue_date": str(date.today()),
        "certificate_number": "CPR-67890",
    }
    response = await async_client.patch(
        f"/training/certifications/{certification.id}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"


async def test_delete_certification(async_client, db_session):
    """Test deleting a certification."""
    from src.models.member import Member
    from src.models.student import Student
    from src.models.certification import Certification
    from src.db.enums import (
        MemberStatus,
        MemberClassification,
        StudentStatus,
        CertificationType,
        CertificationStatus,
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

    certification = Certification(
        student_id=student.id,
        cert_type=CertificationType.FORKLIFT,
        status=CertificationStatus.EXPIRED,
        issue_date=date.today() - timedelta(days=730),
        expiration_date=date.today() - timedelta(days=1),
    )
    db_session.add(certification)
    db_session.commit()

    # Delete it
    response = await async_client.delete(f"/training/certifications/{certification.id}")
    assert response.status_code == 200
