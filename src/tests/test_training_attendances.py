"""Tests for Training Attendances endpoints."""

import uuid
from datetime import date

from src.tests.helpers import create_student, create_course, create_class_session


async def create_attendance(async_client, student_id=None, class_session_id=None):
    """Helper to create an attendance record via API."""
    if student_id is None:
        student = await create_student(async_client)
        student_id = student["id"]
    if class_session_id is None:
        class_session = await create_class_session(async_client)
        class_session_id = class_session["id"]

    payload = {
        "student_id": student_id,
        "class_session_id": class_session_id,
        "status": "present",
    }
    response = await async_client.post("/training/attendances/", json=payload)
    assert response.status_code == 201, f"Failed to create attendance: {response.json()}"
    return response.json()


async def test_create_attendance(async_client):
    """Test creating a new attendance record."""
    student = await create_student(async_client)
    class_session = await create_class_session(async_client)

    payload = {
        "student_id": student["id"],
        "class_session_id": class_session["id"],
        "status": "present",
    }

    response = await async_client.post("/training/attendances/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["student_id"] == student["id"]
    assert data["class_session_id"] == class_session["id"]
    assert data["status"] == "present"


async def test_get_attendance(async_client):
    """Test getting an attendance record by ID."""
    attendance = await create_attendance(async_client)

    response = await async_client.get(f"/training/attendances/{attendance['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == attendance["id"]
    assert data["status"] == "present"


async def test_list_attendances(async_client):
    """Test listing attendance records."""
    response = await async_client.get("/training/attendances/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_update_attendance(async_client):
    """Test updating an attendance record."""
    attendance = await create_attendance(async_client)

    update_payload = {
        "status": "late",
        "arrival_time": "18:15:00",
    }
    response = await async_client.patch(
        f"/training/attendances/{attendance['id']}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "late"


async def test_delete_attendance(async_client):
    """Test deleting an attendance record."""
    attendance = await create_attendance(async_client)

    response = await async_client.delete(f"/training/attendances/{attendance['id']}")
    assert response.status_code == 200
