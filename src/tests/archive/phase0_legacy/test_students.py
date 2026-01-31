import uuid


async def test_create_student(async_client):
    unique = str(uuid.uuid4())[:8]
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": f"john_{unique}@doe.com",
        "phone": "206-555-1212",
        "cohort_id": None,
    }

    response = await async_client.post("/students/", json=payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["first_name"] == "John"


async def test_invalid_email(async_client):
    payload = {
        "first_name": "Test",
        "last_name": "Bad",
        "email": "not-an-email",
        "phone": "206",
        "cohort_id": None,
    }
    response = await async_client.post("/students/", json=payload)
    assert response.status_code == 422
