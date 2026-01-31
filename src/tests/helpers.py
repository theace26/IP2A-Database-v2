"""Test helper functions for creating test data via API."""

import uuid
from datetime import date, time


async def create_member(async_client):
    """Create a member via API and return the response data."""
    unique = str(uuid.uuid4())[:8]
    payload = {
        "member_number": f"M{unique}",
        "first_name": "Test",
        "last_name": "Member",
        "classification": "apprentice_1",
    }
    response = await async_client.post("/members/", json=payload)
    assert response.status_code in (200, 201), f"Failed to create member: {response.json()}"
    return response.json()


async def create_student(async_client, member_id=None):
    """Create a student via API and return the response data."""
    if member_id is None:
        member = await create_member(async_client)
        member_id = member["id"]

    unique = str(uuid.uuid4())[:8]
    payload = {
        "member_id": member_id,
        "student_number": f"S{unique}",
        "status": "enrolled",
        "application_date": str(date.today()),
        "enrollment_date": str(date.today()),
    }
    response = await async_client.post("/training/students/", json=payload)
    assert response.status_code == 201, f"Failed to create student: {response.json()}"
    return response.json()


async def create_course(async_client):
    """Create a course via API and return the response data."""
    unique = str(uuid.uuid4())[:8]
    payload = {
        "code": f"TEST{unique[:4]}",
        "name": "Test Course",
        "course_type": "core",
        "credits": 3.0,
        "hours": 60,
    }
    response = await async_client.post("/training/courses/", json=payload)
    assert response.status_code == 201, f"Failed to create course: {response.json()}"
    return response.json()


async def create_class_session(async_client, course_id=None):
    """Create a class session via API and return the response data."""
    if course_id is None:
        course = await create_course(async_client)
        course_id = course["id"]

    payload = {
        "course_id": course_id,
        "session_date": str(date.today()),
        "start_time": "18:00:00",
        "end_time": "21:00:00",
    }
    response = await async_client.post("/training/class-sessions/", json=payload)
    assert response.status_code == 201, f"Failed to create class session: {response.json()}"
    return response.json()


async def create_enrollment(async_client, student_id=None, course_id=None):
    """Create an enrollment via API and return the response data."""
    if student_id is None:
        student = await create_student(async_client)
        student_id = student["id"]

    if course_id is None:
        course = await create_course(async_client)
        course_id = course["id"]

    payload = {
        "student_id": student_id,
        "course_id": course_id,
        "cohort": "2026-Spring",
        "enrollment_date": str(date.today()),
        "status": "enrolled",
    }
    response = await async_client.post("/training/enrollments/", json=payload)
    assert response.status_code == 201, f"Failed to create enrollment: {response.json()}"
    return response.json()
