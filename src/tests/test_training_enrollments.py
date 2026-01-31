"""Tests for Training Enrollments endpoints."""

import uuid
from datetime import date

from src.tests.helpers import create_student, create_course, create_enrollment


async def test_create_enrollment(async_client):
    """Test creating a new enrollment."""
    student = await create_student(async_client)
    course = await create_course(async_client)

    payload = {
        "student_id": student["id"],
        "course_id": course["id"],
        "cohort": "2026-Spring",
        "enrollment_date": str(date.today()),
        "status": "enrolled",
    }

    response = await async_client.post("/training/enrollments/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["student_id"] == student["id"]
    assert data["course_id"] == course["id"]
    assert data["status"] == "enrolled"


async def test_get_enrollment(async_client):
    """Test getting an enrollment by ID."""
    enrollment = await create_enrollment(async_client)

    response = await async_client.get(f"/training/enrollments/{enrollment['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == enrollment["id"]


async def test_list_enrollments(async_client):
    """Test listing enrollments."""
    response = await async_client.get("/training/enrollments/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_update_enrollment(async_client):
    """Test updating an enrollment."""
    enrollment = await create_enrollment(async_client)

    update_payload = {
        "status": "completed",
        "final_grade": 85.5,
    }
    response = await async_client.patch(
        f"/training/enrollments/{enrollment['id']}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["final_grade"] == 85.5


async def test_delete_enrollment(async_client):
    """Test deleting an enrollment."""
    enrollment = await create_enrollment(async_client)

    response = await async_client.delete(f"/training/enrollments/{enrollment['id']}")
    assert response.status_code == 200
