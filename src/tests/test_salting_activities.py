"""Tests for SALTing Activities endpoints."""

import uuid


# Helper to create a member (required FK)
async def _create_member(async_client):
    unique = str(uuid.uuid4())[:8]
    payload = {
        "member_number": f"M{unique}",
        "first_name": "Salt",
        "last_name": "Worker",
        "classification": "journeyman",
    }
    resp = await async_client.post("/members/", json=payload)
    return resp.json()


# Helper to create an organization (required FK)
async def _create_org(async_client):
    unique = str(uuid.uuid4())[:8]
    payload = {
        "name": f"Target Employer {unique}",
        "org_type": "employer",
    }
    resp = await async_client.post("/organizations/", json=payload)
    return resp.json()


async def test_create_salting_activity(async_client):
    """Test creating a SALTing activity."""
    member = await _create_member(async_client)
    org = await _create_org(async_client)
    payload = {
        "member_id": member["id"],
        "organization_id": org["id"],
        "activity_type": "outreach",
        "activity_date": "2026-01-15",
        "outcome": "positive",
        "workers_contacted": 5,
        "cards_signed": 2,
        "description": "Visited job site, spoke with workers during lunch.",
    }
    response = await async_client.post("/salting-activities/", json=payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["activity_type"] == "outreach"
    assert data["workers_contacted"] == 5
    assert data["cards_signed"] == 2
    assert "id" in data


async def test_get_salting_activity(async_client):
    """Test getting a SALTing activity by ID."""
    member = await _create_member(async_client)
    org = await _create_org(async_client)
    payload = {
        "member_id": member["id"],
        "organization_id": org["id"],
        "activity_type": "leafleting",
        "activity_date": "2026-01-16",
    }
    created = (await async_client.post("/salting-activities/", json=payload)).json()

    response = await async_client.get(f"/salting-activities/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


async def test_get_nonexistent_salting_activity(async_client):
    """Test 404 for non-existent activity."""
    response = await async_client.get("/salting-activities/999999")
    assert response.status_code == 404


async def test_list_salting_activities(async_client):
    """Test listing SALTing activities."""
    response = await async_client.get("/salting-activities/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_update_salting_activity(async_client):
    """Test updating a SALTing activity."""
    member = await _create_member(async_client)
    org = await _create_org(async_client)
    payload = {
        "member_id": member["id"],
        "organization_id": org["id"],
        "activity_type": "meeting",
        "activity_date": "2026-01-17",
        "workers_contacted": 3,
    }
    created = (await async_client.post("/salting-activities/", json=payload)).json()

    update_payload = {"outcome": "positive", "workers_contacted": 10, "cards_signed": 4}
    response = await async_client.put(
        f"/salting-activities/{created['id']}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["outcome"] == "positive"
    assert data["workers_contacted"] == 10
    assert data["cards_signed"] == 4


async def test_delete_salting_activity(async_client):
    """Test deleting a SALTing activity."""
    member = await _create_member(async_client)
    org = await _create_org(async_client)
    payload = {
        "member_id": member["id"],
        "organization_id": org["id"],
        "activity_type": "one_on_one",
        "activity_date": "2026-01-18",
    }
    created = (await async_client.post("/salting-activities/", json=payload)).json()

    response = await async_client.delete(f"/salting-activities/{created['id']}")
    assert response.status_code == 200

    get_resp = await async_client.get(f"/salting-activities/{created['id']}")
    assert get_resp.status_code == 404


async def test_invalid_activity_type(async_client):
    """Test validation error for invalid activity type."""
    member = await _create_member(async_client)
    org = await _create_org(async_client)
    payload = {
        "member_id": member["id"],
        "organization_id": org["id"],
        "activity_type": "invalid_type",
        "activity_date": "2026-01-19",
    }
    response = await async_client.post("/salting-activities/", json=payload)
    assert response.status_code == 422
