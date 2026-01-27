"""Tests for Organizations endpoints."""

import uuid


async def test_create_organization(async_client):
    """Test creating a new organization."""
    unique = str(uuid.uuid4())[:8]
    payload = {
        "name": f"Test Organization {unique}",
        "org_type": "employer",
        "address": "123 Main St",
        "city": "Seattle",
        "state": "WA",
        "zip_code": "98101",
        "phone": "206-555-1234",
        "email": f"test_{unique}@example.com",
        "website": "https://example.com",
        "salting_score": 3,
        "salting_notes": "Test notes",
    }

    response = await async_client.post("/organizations/", json=payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["org_type"] == "employer"
    assert data["city"] == "Seattle"
    assert "id" in data


async def test_get_organization(async_client):
    """Test getting an organization by ID."""
    # Create organization first
    unique = str(uuid.uuid4())[:8]
    payload = {
        "name": f"Test Org {unique}",
        "org_type": "union",
    }
    create_response = await async_client.post("/organizations/", json=payload)
    created = create_response.json()

    # Get the organization
    response = await async_client.get(f"/organizations/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["name"] == payload["name"]


async def test_get_nonexistent_organization(async_client):
    """Test getting a non-existent organization returns 404."""
    response = await async_client.get("/organizations/999999")
    assert response.status_code == 404


async def test_list_organizations(async_client):
    """Test listing organizations."""
    response = await async_client.get("/organizations/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_update_organization(async_client):
    """Test updating an organization."""
    # Create organization first
    unique = str(uuid.uuid4())[:8]
    payload = {
        "name": f"Original Name {unique}",
        "org_type": "employer",
    }
    create_response = await async_client.post("/organizations/", json=payload)
    created = create_response.json()

    # Update it
    update_payload = {
        "name": f"Updated Name {unique}",
        "city": "Portland",
    }
    response = await async_client.put(
        f"/organizations/{created['id']}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_payload["name"]
    assert data["city"] == "Portland"


async def test_delete_organization(async_client):
    """Test deleting an organization."""
    # Create organization first
    unique = str(uuid.uuid4())[:8]
    payload = {
        "name": f"To Delete {unique}",
        "org_type": "jatc",
    }
    create_response = await async_client.post("/organizations/", json=payload)
    created = create_response.json()

    # Delete it
    response = await async_client.delete(f"/organizations/{created['id']}")
    assert response.status_code == 200

    # Verify it's gone
    get_response = await async_client.get(f"/organizations/{created['id']}")
    assert get_response.status_code == 404


async def test_invalid_email_organization(async_client):
    """Test that invalid email returns validation error."""
    payload = {
        "name": "Invalid Email Org",
        "org_type": "employer",
        "email": "not-an-email",
    }
    response = await async_client.post("/organizations/", json=payload)
    assert response.status_code == 422
