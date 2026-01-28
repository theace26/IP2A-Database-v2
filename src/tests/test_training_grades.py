"""Tests for Training Grades endpoints."""

import uuid
from datetime import date

from src.tests.helpers import create_student, create_course


async def create_grade(async_client, student_id=None, course_id=None):
    """Helper to create a grade via API."""
    if student_id is None:
        student = await create_student(async_client)
        student_id = student["id"]
    if course_id is None:
        course = await create_course(async_client)
        course_id = course["id"]

    payload = {
        "student_id": student_id,
        "course_id": course_id,
        "grade_type": "quiz",
        "name": "Quiz 1",
        "points_earned": 90.0,
        "points_possible": 100.0,
        "weight": 1.0,
        "grade_date": str(date.today()),
    }
    response = await async_client.post("/training/grades/", json=payload)
    assert response.status_code == 201, f"Failed to create grade: {response.json()}"
    return response.json()


async def test_create_grade(async_client):
    """Test creating a new grade."""
    student = await create_student(async_client)
    course = await create_course(async_client)

    payload = {
        "student_id": student["id"],
        "course_id": course["id"],
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
    assert data["student_id"] == student["id"]
    assert data["course_id"] == course["id"]
    assert data["points_earned"] == 85.0
    assert data["grade_type"] == "exam"


async def test_get_grade(async_client):
    """Test getting a grade by ID."""
    grade = await create_grade(async_client)

    response = await async_client.get(f"/training/grades/{grade['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == grade["id"]
    assert data["name"] == "Quiz 1"


async def test_list_grades(async_client):
    """Test listing grades."""
    response = await async_client.get("/training/grades/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_update_grade(async_client):
    """Test updating a grade."""
    grade = await create_grade(async_client)

    update_payload = {
        "points_earned": 95.0,
        "feedback": "Excellent work!",
    }
    response = await async_client.patch(f"/training/grades/{grade['id']}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["points_earned"] == 95.0


async def test_delete_grade(async_client):
    """Test deleting a grade."""
    grade = await create_grade(async_client)

    response = await async_client.delete(f"/training/grades/{grade['id']}")
    assert response.status_code == 200
