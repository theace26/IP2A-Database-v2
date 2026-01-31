import uuid


async def test_create_instructor(async_client):
    unique = str(uuid.uuid4())[:8]
    payload = {
        "first_name": "Alice",
        "last_name": "Johnson",
        "email": f"alice_{unique}@ibew.org",
        "phone": "206-555-0000",
        "certification": "Master Electrician",
    }
    response = await async_client.post("/instructors/", json=payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["first_name"] == "Alice"


async def test_instructor_list(async_client):
    response = await async_client.get("/instructors/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
