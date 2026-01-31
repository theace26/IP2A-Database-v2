"""Tests for Training Certifications endpoints."""

import uuid
from datetime import date, timedelta

from src.tests.helpers import create_student


async def create_certification(async_client, student_id=None):
    """Helper to create a certification via API."""
    if student_id is None:
        student = await create_student(async_client)
        student_id = student["id"]

    payload = {
        "student_id": student_id,
        "cert_type": "first_aid",
        "status": "active",
        "issue_date": str(date.today()),
        "expiration_date": str(date.today() + timedelta(days=365)),
        "certificate_number": f"FA-{uuid.uuid4().hex[:8]}",
        "issuing_organization": "Red Cross",
    }
    response = await async_client.post("/training/certifications/", json=payload)
    assert response.status_code == 201, f"Failed to create certification: {response.json()}"
    return response.json()


async def test_create_certification(async_client):
    """Test creating a new certification."""
    student = await create_student(async_client)

    payload = {
        "student_id": student["id"],
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
    assert data["student_id"] == student["id"]
    assert data["cert_type"] == "osha_10"
    assert data["status"] == "active"


async def test_get_certification(async_client):
    """Test getting a certification by ID."""
    certification = await create_certification(async_client)

    response = await async_client.get(f"/training/certifications/{certification['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == certification["id"]
    assert data["cert_type"] == "first_aid"


async def test_list_certifications(async_client):
    """Test listing certifications."""
    response = await async_client.get("/training/certifications/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_update_certification(async_client):
    """Test updating a certification."""
    # Create certification with pending status
    student = await create_student(async_client)
    payload = {
        "student_id": student["id"],
        "cert_type": "cpr",
        "status": "pending",
    }
    response = await async_client.post("/training/certifications/", json=payload)
    assert response.status_code == 201
    certification = response.json()

    # Update it
    update_payload = {
        "status": "active",
        "issue_date": str(date.today()),
        "certificate_number": "CPR-67890",
    }
    response = await async_client.patch(
        f"/training/certifications/{certification['id']}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"


async def test_delete_certification(async_client):
    """Test deleting a certification."""
    certification = await create_certification(async_client)

    response = await async_client.delete(f"/training/certifications/{certification['id']}")
    assert response.status_code == 200
