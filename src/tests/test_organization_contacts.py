"""Tests for OrganizationContacts endpoints."""

import uuid


async def test_create_organization_contact(async_client):
    """Test creating a new organization contact."""
    # First create an organization
    unique = str(uuid.uuid4())[:8]
    org_payload = {
        "name": f"Test Org {unique}",
        "org_type": "employer",
    }
    org_response = await async_client.post("/organizations/", json=org_payload)
    org = org_response.json()

    # Create contact
    contact_payload = {
        "organization_id": org["id"],
        "first_name": "Jane",
        "last_name": "Smith",
        "title": "Manager",
        "phone": "206-555-5678",
        "email": f"jane_{unique}@example.com",
        "is_primary": True,
        "notes": "Primary contact",
    }

    response = await async_client.post("/organization-contacts/", json=contact_payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Smith"
    assert data["organization_id"] == org["id"]
    assert data["is_primary"] is True
    assert "id" in data


async def test_get_organization_contact(async_client):
    """Test getting an organization contact by ID."""
    # Create organization and contact
    unique = str(uuid.uuid4())[:8]
    org_payload = {"name": f"Test Org {unique}", "org_type": "union"}
    org_response = await async_client.post("/organizations/", json=org_payload)
    org = org_response.json()

    contact_payload = {
        "organization_id": org["id"],
        "first_name": "John",
        "last_name": "Doe",
    }
    create_response = await async_client.post(
        "/organization-contacts/", json=contact_payload
    )
    created = create_response.json()

    # Get the contact
    response = await async_client.get(f"/organization-contacts/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["first_name"] == "John"


async def test_get_nonexistent_contact(async_client):
    """Test getting a non-existent contact returns 404."""
    response = await async_client.get("/organization-contacts/999999")
    assert response.status_code == 404


async def test_list_organization_contacts(async_client):
    """Test listing organization contacts."""
    response = await async_client.get("/organization-contacts/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_update_organization_contact(async_client):
    """Test updating an organization contact."""
    # Create organization and contact
    unique = str(uuid.uuid4())[:8]
    org_payload = {"name": f"Test Org {unique}", "org_type": "employer"}
    org_response = await async_client.post("/organizations/", json=org_payload)
    org = org_response.json()

    contact_payload = {
        "organization_id": org["id"],
        "first_name": "Original",
        "last_name": "Name",
    }
    create_response = await async_client.post(
        "/organization-contacts/", json=contact_payload
    )
    created = create_response.json()

    # Update it
    update_payload = {
        "first_name": "Updated",
        "title": "Director",
    }
    response = await async_client.put(
        f"/organization-contacts/{created['id']}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["title"] == "Director"


async def test_delete_organization_contact(async_client):
    """Test deleting an organization contact."""
    # Create organization and contact
    unique = str(uuid.uuid4())[:8]
    org_payload = {"name": f"Test Org {unique}", "org_type": "jatc"}
    org_response = await async_client.post("/organizations/", json=org_payload)
    org = org_response.json()

    contact_payload = {
        "organization_id": org["id"],
        "first_name": "To",
        "last_name": "Delete",
    }
    create_response = await async_client.post(
        "/organization-contacts/", json=contact_payload
    )
    created = create_response.json()

    # Delete it
    response = await async_client.delete(f"/organization-contacts/{created['id']}")
    assert response.status_code == 200

    # Verify it's gone
    get_response = await async_client.get(f"/organization-contacts/{created['id']}")
    assert get_response.status_code == 404


async def test_invalid_email_contact(async_client):
    """Test that invalid email returns validation error."""
    unique = str(uuid.uuid4())[:8]
    org_payload = {"name": f"Test Org {unique}", "org_type": "employer"}
    org_response = await async_client.post("/organizations/", json=org_payload)
    org = org_response.json()

    payload = {
        "organization_id": org["id"],
        "first_name": "Test",
        "last_name": "User",
        "email": "not-an-email",
    }
    response = await async_client.post("/organization-contacts/", json=payload)
    assert response.status_code == 422
