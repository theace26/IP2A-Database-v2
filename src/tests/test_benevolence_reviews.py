"""Tests for Benevolence Reviews endpoints."""

import uuid


async def _create_member(async_client):
    unique = str(uuid.uuid4())[:8]
    payload = {
        "member_number": f"M{unique}",
        "first_name": "Review",
        "last_name": "Subject",
        "classification": "journeyman",
    }
    resp = await async_client.post("/members/", json=payload)
    return resp.json()


async def _create_application(async_client, member_id):
    payload = {
        "member_id": member_id,
        "application_date": "2026-01-20",
        "reason": "medical",
        "description": "Medical expenses.",
        "amount_requested": "2000.00",
        "status": "submitted",
    }
    resp = await async_client.post("/benevolence-applications/", json=payload)
    return resp.json()


async def test_create_benevolence_review(async_client):
    """Test creating a benevolence review."""
    member = await _create_member(async_client)
    app = await _create_application(async_client, member["id"])
    payload = {
        "application_id": app["id"],
        "reviewer_name": "John Smith, VP",
        "review_level": "vp",
        "decision": "approved",
        "review_date": "2026-01-25",
        "comments": "Application meets criteria. Recommend approval.",
    }
    response = await async_client.post("/benevolence-reviews/", json=payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["review_level"] == "vp"
    assert data["decision"] == "approved"
    assert "id" in data


async def test_get_benevolence_review(async_client):
    """Test getting a review by ID."""
    member = await _create_member(async_client)
    app = await _create_application(async_client, member["id"])
    payload = {
        "application_id": app["id"],
        "reviewer_name": "Jane Doe, Admin",
        "review_level": "admin",
        "decision": "needs_info",
        "review_date": "2026-01-26",
    }
    created = (await async_client.post("/benevolence-reviews/", json=payload)).json()

    response = await async_client.get(f"/benevolence-reviews/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


async def test_get_nonexistent_review(async_client):
    """Test 404 for non-existent review."""
    response = await async_client.get("/benevolence-reviews/999999")
    assert response.status_code == 404


async def test_list_benevolence_reviews(async_client):
    """Test listing reviews."""
    response = await async_client.get("/benevolence-reviews/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_list_reviews_by_application(async_client):
    """Test listing reviews for a specific application."""
    member = await _create_member(async_client)
    app = await _create_application(async_client, member["id"])

    # Create two reviews for the same application
    for level, decision in [("vp", "approved"), ("president", "approved")]:
        payload = {
            "application_id": app["id"],
            "reviewer_name": f"Reviewer {level}",
            "review_level": level,
            "decision": decision,
            "review_date": "2026-01-27",
        }
        await async_client.post("/benevolence-reviews/", json=payload)

    response = await async_client.get(
        f"/benevolence-reviews/by-application/{app['id']}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


async def test_update_benevolence_review(async_client):
    """Test updating a review."""
    member = await _create_member(async_client)
    app = await _create_application(async_client, member["id"])
    payload = {
        "application_id": app["id"],
        "reviewer_name": "Original Reviewer",
        "review_level": "manager",
        "decision": "deferred",
        "review_date": "2026-01-28",
    }
    created = (await async_client.post("/benevolence-reviews/", json=payload)).json()

    update_payload = {"decision": "approved", "comments": "Reconsidered. Approved."}
    response = await async_client.put(
        f"/benevolence-reviews/{created['id']}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "approved"
    assert data["comments"] == "Reconsidered. Approved."


async def test_delete_benevolence_review(async_client):
    """Test deleting a review."""
    member = await _create_member(async_client)
    app = await _create_application(async_client, member["id"])
    payload = {
        "application_id": app["id"],
        "reviewer_name": "To Delete",
        "review_level": "vp",
        "decision": "denied",
        "review_date": "2026-01-29",
    }
    created = (await async_client.post("/benevolence-reviews/", json=payload)).json()

    response = await async_client.delete(f"/benevolence-reviews/{created['id']}")
    assert response.status_code == 200

    get_resp = await async_client.get(f"/benevolence-reviews/{created['id']}")
    assert get_resp.status_code == 404
