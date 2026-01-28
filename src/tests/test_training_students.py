"""Tests for Training Students endpoints."""

import uuid
from datetime import date


async def _create_member(async_client):
    """Helper to create a member via API."""
    unique = str(uuid.uuid4())[:8]
    payload = {
        "member_number": f"M{unique}",
        "first_name": "Test",
        "last_name": "Student",
        "classification": "apprentice_1",
    }
    response = await async_client.post("/members/", json=payload)
    assert response.status_code in (200, 201)
    return response.json()


async def test_create_student(async_client):
    """Test creating a new student."""
    # First create a member via API
    member = await _create_member(async_client)

    unique = str(uuid.uuid4())[:8]
    payload = {
        "member_id": member["id"],
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


async def test_get_student(async_client):
    """Test getting a student by ID."""
    # Create member and student via API
    member = await _create_member(async_client)

    unique = str(uuid.uuid4())[:8]
    payload = {
        "member_id": member["id"],
        "student_number": f"S{unique}",
        "status": "enrolled",
        "application_date": str(date.today()),
        "enrollment_date": str(date.today()),
    }
    create_response = await async_client.post("/training/students/", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()

    response = await async_client.get(f"/training/students/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["student_number"] == payload["student_number"]


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


async def test_update_student(async_client):
    """Test updating a student."""
    # Create member and student via API
    member = await _create_member(async_client)

    unique = str(uuid.uuid4())[:8]
    payload = {
        "member_id": member["id"],
        "student_number": f"S{unique}",
        "status": "applicant",
        "application_date": str(date.today()),
    }
    create_response = await async_client.post("/training/students/", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()

    # Update it
    update_payload = {
        "status": "enrolled",
        "enrollment_date": str(date.today()),
    }
    response = await async_client.patch(
        f"/training/students/{created['id']}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "enrolled"


async def test_delete_student(async_client):
    """Test deleting a student."""
    # Create member and student via API
    member = await _create_member(async_client)

    unique = str(uuid.uuid4())[:8]
    payload = {
        "member_id": member["id"],
        "student_number": f"S{unique}",
        "status": "applicant",
        "application_date": str(date.today()),
    }
    create_response = await async_client.post("/training/students/", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()

    # Delete it
    response = await async_client.delete(f"/training/students/{created['id']}")
    assert response.status_code == 200


async def test_generate_student_number(async_client):
    """Test generating next student number."""
    response = await async_client.get("/training/students/generate-number")
    assert response.status_code == 200
    data = response.json()
    assert "student_number" in data
    # Student numbers start with year prefix
    assert len(data["student_number"]) > 0
