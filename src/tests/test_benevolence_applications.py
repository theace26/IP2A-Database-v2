"""Tests for Benevolence Applications endpoints."""

import uuid


async def _create_member(async_client):
    unique = str(uuid.uuid4())[:8]
    payload = {
        "member_number": f"M{unique}",
        "first_name": "Ben",
        "last_name": "Applicant",
        "classification": "journeyman",
    }
    resp = await async_client.post("/members/", json=payload)
    return resp.json()


async def test_create_benevolence_application(async_client):
    """Test creating a benevolence application."""
    member = await _create_member(async_client)
    payload = {
        "member_id": member["id"],
        "application_date": "2026-01-20",
        "reason": "medical",
        "description": "Emergency surgery costs not covered by insurance.",
        "amount_requested": "2500.00",
        "status": "submitted",
    }
    response = await async_client.post("/benevolence-applications/", json=payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["reason"] == "medical"
    assert float(data["amount_requested"]) == 2500.00
    assert data["status"] == "submitted"
    assert "id" in data


async def test_get_benevolence_application(async_client):
    """Test getting a benevolence application by ID."""
    member = await _create_member(async_client)
    payload = {
        "member_id": member["id"],
        "application_date": "2026-01-21",
        "reason": "hardship",
        "description": "Lost home in fire.",
        "amount_requested": "5000.00",
    }
    created = (
        await async_client.post("/benevolence-applications/", json=payload)
    ).json()

    response = await async_client.get(f"/benevolence-applications/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


async def test_get_nonexistent_application(async_client):
    """Test 404 for non-existent application."""
    response = await async_client.get("/benevolence-applications/999999")
    assert response.status_code == 404


async def test_list_benevolence_applications(async_client):
    """Test listing benevolence applications."""
    response = await async_client.get("/benevolence-applications/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_update_benevolence_application(async_client):
    """Test updating a benevolence application."""
    member = await _create_member(async_client)
    payload = {
        "member_id": member["id"],
        "application_date": "2026-01-22",
        "reason": "death_in_family",
        "description": "Funeral expenses for spouse.",
        "amount_requested": "3000.00",
    }
    created = (
        await async_client.post("/benevolence-applications/", json=payload)
    ).json()

    update_payload = {
        "status": "approved",
        "approved_amount": "2500.00",
    }
    response = await async_client.put(
        f"/benevolence-applications/{created['id']}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert float(data["approved_amount"]) == 2500.00


async def test_delete_benevolence_application(async_client):
    """Test deleting a benevolence application."""
    member = await _create_member(async_client)
    payload = {
        "member_id": member["id"],
        "application_date": "2026-01-23",
        "reason": "disaster",
        "description": "Flood damage to home.",
        "amount_requested": "4000.00",
    }
    created = (
        await async_client.post("/benevolence-applications/", json=payload)
    ).json()

    response = await async_client.delete(f"/benevolence-applications/{created['id']}")
    assert response.status_code == 200

    get_resp = await async_client.get(f"/benevolence-applications/{created['id']}")
    assert get_resp.status_code == 404


async def test_invalid_reason(async_client):
    """Test validation error for invalid reason."""
    member = await _create_member(async_client)
    payload = {
        "member_id": member["id"],
        "application_date": "2026-01-24",
        "reason": "vacation",
        "description": "Not a valid reason.",
        "amount_requested": "1000.00",
    }
    response = await async_client.post("/benevolence-applications/", json=payload)
    assert response.status_code == 422
