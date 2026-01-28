"""Tests for MemberEmployments endpoints."""

import uuid


async def test_create_member_employment(async_client):
    """Test creating a new member employment record."""
    # Create member and organization first
    unique = str(uuid.uuid4())[:8]

    member_payload = {
        "member_number": f"M{unique}",
        "first_name": "Test",
        "last_name": "Member",
        "classification": "journeyman",
    }
    member_response = await async_client.post("/members/", json=member_payload)
    member = member_response.json()

    org_payload = {
        "name": f"Test Employer {unique}",
        "org_type": "employer",
    }
    org_response = await async_client.post("/organizations/", json=org_payload)
    org = org_response.json()

    # Create employment record
    employment_payload = {
        "member_id": member["id"],
        "organization_id": org["id"],
        "start_date": "2024-01-01",
        "job_title": "Electrician",
        "hourly_rate": 45.50,
        "is_current": True,
    }

    response = await async_client.post("/member-employments/", json=employment_payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["member_id"] == member["id"]
    assert data["organization_id"] == org["id"]
    assert data["job_title"] == "Electrician"
    assert float(data["hourly_rate"]) == 45.50
    assert data["is_current"] is True
    assert "id" in data


async def test_get_member_employment(async_client):
    """Test getting a member employment record by ID."""
    # Create member, organization, and employment
    unique = str(uuid.uuid4())[:8]

    member_payload = {
        "member_number": f"M{unique}",
        "first_name": "Test",
        "last_name": "Member",
        "classification": "apprentice_1",
    }
    member_response = await async_client.post("/members/", json=member_payload)
    member = member_response.json()

    org_payload = {"name": f"Test Org {unique}", "org_type": "employer"}
    org_response = await async_client.post("/organizations/", json=org_payload)
    org = org_response.json()

    employment_payload = {
        "member_id": member["id"],
        "organization_id": org["id"],
        "start_date": "2024-06-01",
    }
    create_response = await async_client.post(
        "/member-employments/", json=employment_payload
    )
    created = create_response.json()

    # Get the employment record
    response = await async_client.get(f"/member-employments/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["member_id"] == member["id"]


async def test_list_member_employments_by_member(async_client):
    """Test listing all employment records for a specific member."""
    # Create member and organizations
    unique = str(uuid.uuid4())[:8]

    member_payload = {
        "member_number": f"M{unique}",
        "first_name": "Test",
        "last_name": "Member",
        "classification": "journeyman",
    }
    member_response = await async_client.post("/members/", json=member_payload)
    member = member_response.json()

    # Create two organizations
    org1_payload = {"name": f"Employer 1 {unique}", "org_type": "employer"}
    org1_response = await async_client.post("/organizations/", json=org1_payload)
    org1 = org1_response.json()

    org2_payload = {"name": f"Employer 2 {unique}", "org_type": "employer"}
    org2_response = await async_client.post("/organizations/", json=org2_payload)
    org2 = org2_response.json()

    # Create two employment records for the member
    emp1_payload = {
        "member_id": member["id"],
        "organization_id": org1["id"],
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "is_current": False,
    }
    await async_client.post("/member-employments/", json=emp1_payload)

    emp2_payload = {
        "member_id": member["id"],
        "organization_id": org2["id"],
        "start_date": "2024-01-01",
        "is_current": True,
    }
    await async_client.post("/member-employments/", json=emp2_payload)

    # List employments for this member
    response = await async_client.get(f"/member-employments/by-member/{member['id']}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    for emp in data:
        assert emp["member_id"] == member["id"]


async def test_get_nonexistent_employment(async_client):
    """Test getting a non-existent employment returns 404."""
    response = await async_client.get("/member-employments/999999")
    assert response.status_code == 404


async def test_list_member_employments(async_client):
    """Test listing all member employments."""
    response = await async_client.get("/member-employments/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_update_member_employment(async_client):
    """Test updating a member employment record."""
    # Create member, organization, and employment
    unique = str(uuid.uuid4())[:8]

    member_payload = {
        "member_number": f"M{unique}",
        "first_name": "Test",
        "last_name": "Member",
        "classification": "journeyman",
    }
    member_response = await async_client.post("/members/", json=member_payload)
    member = member_response.json()

    org_payload = {"name": f"Test Org {unique}", "org_type": "employer"}
    org_response = await async_client.post("/organizations/", json=org_payload)
    org = org_response.json()

    employment_payload = {
        "member_id": member["id"],
        "organization_id": org["id"],
        "start_date": "2024-01-01",
        "is_current": True,
    }
    create_response = await async_client.post(
        "/member-employments/", json=employment_payload
    )
    created = create_response.json()

    # Update it
    update_payload = {
        "end_date": "2024-12-31",
        "is_current": False,
        "hourly_rate": 50.00,
    }
    response = await async_client.put(
        f"/member-employments/{created['id']}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["end_date"] == "2024-12-31"
    assert data["is_current"] is False
    assert float(data["hourly_rate"]) == 50.00


async def test_delete_member_employment(async_client):
    """Test deleting a member employment record."""
    # Create member, organization, and employment
    unique = str(uuid.uuid4())[:8]

    member_payload = {
        "member_number": f"M{unique}",
        "first_name": "Test",
        "last_name": "Member",
        "classification": "apprentice_1",
    }
    member_response = await async_client.post("/members/", json=member_payload)
    member = member_response.json()

    org_payload = {"name": f"Test Org {unique}", "org_type": "employer"}
    org_response = await async_client.post("/organizations/", json=org_payload)
    org = org_response.json()

    employment_payload = {
        "member_id": member["id"],
        "organization_id": org["id"],
        "start_date": "2024-01-01",
    }
    create_response = await async_client.post(
        "/member-employments/", json=employment_payload
    )
    created = create_response.json()

    # Delete it
    response = await async_client.delete(f"/member-employments/{created['id']}")
    assert response.status_code == 200

    # Verify it's gone
    get_response = await async_client.get(f"/member-employments/{created['id']}")
    assert get_response.status_code == 404
