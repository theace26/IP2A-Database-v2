"""Tests for Training Courses endpoints."""

import uuid


async def test_create_course(async_client):
    """Test creating a new course."""
    unique = str(uuid.uuid4())[:8]
    payload = {
        "code": f"TEST{unique[:4]}",
        "name": "Test Course",
        "description": "A test course description",
        "course_type": "core",
        "credits": 3.0,
        "hours": 60,
        "is_required": True,
        "passing_grade": 70.0,
    }

    response = await async_client.post("/training/courses/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == payload["code"]
    assert data["name"] == "Test Course"
    assert data["credits"] == 3.0
    assert "id" in data


async def test_get_course(async_client):
    """Test getting a course by ID."""
    # Create course via API first
    unique = str(uuid.uuid4())[:8]
    payload = {
        "code": f"TEST{unique[:4]}",
        "name": "Test Course",
        "course_type": "core",
        "credits": 3.0,
        "hours": 60,
    }
    create_response = await async_client.post("/training/courses/", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()

    # Get the course
    response = await async_client.get(f"/training/courses/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["code"] == payload["code"]


async def test_get_nonexistent_course(async_client):
    """Test getting a non-existent course returns 404."""
    response = await async_client.get("/training/courses/999999")
    assert response.status_code == 404


async def test_list_courses(async_client):
    """Test listing courses."""
    response = await async_client.get("/training/courses/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_update_course(async_client):
    """Test updating a course."""
    # Create course via API first
    unique = str(uuid.uuid4())[:8]
    payload = {
        "code": f"TEST{unique[:4]}",
        "name": "Original Name",
        "course_type": "core",
        "credits": 3.0,
        "hours": 60,
    }
    create_response = await async_client.post("/training/courses/", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()

    # Update it
    update_payload = {
        "name": "Updated Name",
        "is_active": False,
    }
    response = await async_client.patch(
        f"/training/courses/{created['id']}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["is_active"] is False


async def test_delete_course(async_client):
    """Test deleting a course."""
    # Create course via API first
    unique = str(uuid.uuid4())[:8]
    payload = {
        "code": f"TEST{unique[:4]}",
        "name": "Test Course",
        "course_type": "elective",
        "credits": 2.0,
        "hours": 40,
    }
    create_response = await async_client.post("/training/courses/", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()

    # Delete it
    response = await async_client.delete(f"/training/courses/{created['id']}")
    assert response.status_code == 200
