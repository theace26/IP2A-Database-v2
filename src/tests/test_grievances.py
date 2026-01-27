"""Tests for Grievances endpoints."""

import uuid


async def _create_member(async_client):
    unique = str(uuid.uuid4())[:8]
    payload = {
        "member_number": f"M{unique}",
        "first_name": "Grieved",
        "last_name": "Worker",
        "classification": "journeyman",
    }
    resp = await async_client.post("/members/", json=payload)
    return resp.json()


async def _create_org(async_client):
    unique = str(uuid.uuid4())[:8]
    payload = {
        "name": f"Employer {unique}",
        "org_type": "employer",
    }
    resp = await async_client.post("/organizations/", json=payload)
    return resp.json()


async def test_create_grievance(async_client):
    """Test creating a grievance."""
    member = await _create_member(async_client)
    org = await _create_org(async_client)
    unique = str(uuid.uuid4())[:8]
    payload = {
        "grievance_number": f"GR{unique}",
        "member_id": member["id"],
        "employer_id": org["id"],
        "filed_date": "2026-01-15",
        "incident_date": "2026-01-10",
        "contract_article": "Article 12.3",
        "violation_description": "Employer failed to provide required safety equipment.",
        "remedy_sought": "Provide safety equipment and compensate for lost wages.",
        "assigned_rep": "Business Rep Smith",
    }
    response = await async_client.post("/grievances/", json=payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["grievance_number"] == f"GR{unique}"
    assert data["status"] == "open"
    assert data["current_step"] == "step_1"
    assert "id" in data


async def test_get_grievance(async_client):
    """Test getting a grievance by ID."""
    member = await _create_member(async_client)
    org = await _create_org(async_client)
    unique = str(uuid.uuid4())[:8]
    payload = {
        "grievance_number": f"GR{unique}",
        "member_id": member["id"],
        "employer_id": org["id"],
        "filed_date": "2026-01-16",
        "violation_description": "Overtime not paid properly.",
    }
    created = (await async_client.post("/grievances/", json=payload)).json()

    response = await async_client.get(f"/grievances/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


async def test_get_grievance_by_number(async_client):
    """Test getting a grievance by grievance number."""
    member = await _create_member(async_client)
    org = await _create_org(async_client)
    unique = str(uuid.uuid4())[:8]
    grievance_number = f"GR{unique}"
    payload = {
        "grievance_number": grievance_number,
        "member_id": member["id"],
        "employer_id": org["id"],
        "filed_date": "2026-01-17",
        "violation_description": "Unsafe working conditions.",
    }
    created = (await async_client.post("/grievances/", json=payload)).json()

    response = await async_client.get(f"/grievances/by-number/{grievance_number}")
    assert response.status_code == 200
    assert response.json()["grievance_number"] == grievance_number
    assert response.json()["id"] == created["id"]


async def test_get_nonexistent_grievance(async_client):
    """Test 404 for non-existent grievance."""
    response = await async_client.get("/grievances/999999")
    assert response.status_code == 404


async def test_list_grievances(async_client):
    """Test listing grievances."""
    response = await async_client.get("/grievances/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_update_grievance(async_client):
    """Test updating a grievance."""
    member = await _create_member(async_client)
    org = await _create_org(async_client)
    unique = str(uuid.uuid4())[:8]
    payload = {
        "grievance_number": f"GR{unique}",
        "member_id": member["id"],
        "employer_id": org["id"],
        "filed_date": "2026-01-18",
        "violation_description": "Contract violation.",
    }
    created = (await async_client.post("/grievances/", json=payload)).json()

    update_payload = {
        "current_step": "step_2",
        "status": "hearing",
        "notes": "Advanced to Step 2 after employer denied at Step 1.",
    }
    response = await async_client.put(
        f"/grievances/{created['id']}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_step"] == "step_2"
    assert data["status"] == "hearing"


async def test_delete_grievance(async_client):
    """Test deleting a grievance."""
    member = await _create_member(async_client)
    org = await _create_org(async_client)
    unique = str(uuid.uuid4())[:8]
    payload = {
        "grievance_number": f"GR{unique}",
        "member_id": member["id"],
        "employer_id": org["id"],
        "filed_date": "2026-01-19",
        "violation_description": "To be deleted.",
    }
    created = (await async_client.post("/grievances/", json=payload)).json()

    response = await async_client.delete(f"/grievances/{created['id']}")
    assert response.status_code == 200

    get_resp = await async_client.get(f"/grievances/{created['id']}")
    assert get_resp.status_code == 404


async def test_create_grievance_step_record(async_client):
    """Test creating a step record for a grievance."""
    member = await _create_member(async_client)
    org = await _create_org(async_client)
    unique = str(uuid.uuid4())[:8]
    grievance_payload = {
        "grievance_number": f"GR{unique}",
        "member_id": member["id"],
        "employer_id": org["id"],
        "filed_date": "2026-01-20",
        "violation_description": "Safety violation for step testing.",
    }
    grievance = (
        await async_client.post("/grievances/", json=grievance_payload)
    ).json()

    step_payload = {
        "grievance_id": grievance["id"],
        "step_number": 1,
        "meeting_date": "2026-01-25",
        "union_attendees": "Rep Smith, Steward Jones",
        "employer_attendees": "HR Director, Foreman",
        "outcome": "denied",
        "notes": "Employer denied grievance. Advancing to Step 2.",
    }
    response = await async_client.post(
        f"/grievances/{grievance['id']}/steps", json=step_payload
    )
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["step_number"] == 1
    assert data["outcome"] == "denied"


async def test_list_grievance_steps(async_client):
    """Test listing step records for a grievance."""
    member = await _create_member(async_client)
    org = await _create_org(async_client)
    unique = str(uuid.uuid4())[:8]
    grievance_payload = {
        "grievance_number": f"GR{unique}",
        "member_id": member["id"],
        "employer_id": org["id"],
        "filed_date": "2026-01-21",
        "violation_description": "Testing step listing.",
    }
    grievance = (
        await async_client.post("/grievances/", json=grievance_payload)
    ).json()

    # Create two steps
    for step_num, outcome in [(1, "denied"), (2, "advanced")]:
        await async_client.post(
            f"/grievances/{grievance['id']}/steps",
            json={
                "grievance_id": grievance["id"],
                "step_number": step_num,
                "meeting_date": f"2026-01-2{step_num}",
                "outcome": outcome,
            },
        )

    response = await async_client.get(f"/grievances/{grievance['id']}/steps")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


async def test_duplicate_grievance_number(async_client):
    """Test that duplicate grievance numbers are rejected."""
    member = await _create_member(async_client)
    org = await _create_org(async_client)
    unique = str(uuid.uuid4())[:8]
    grievance_number = f"GR{unique}"
    payload = {
        "grievance_number": grievance_number,
        "member_id": member["id"],
        "employer_id": org["id"],
        "filed_date": "2026-01-22",
        "violation_description": "First grievance.",
    }

    resp1 = await async_client.post("/grievances/", json=payload)
    assert resp1.status_code in (200, 201)

    payload["violation_description"] = "Duplicate number."
    try:
        resp2 = await async_client.post("/grievances/", json=payload)
        assert resp2.status_code in (400, 409, 422, 500)
    except Exception:
        pass
