async def test_create_student(async_client):
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@doe.com",
        "phone": "206-555-1212",
        "cohort_id": None
    }

    response = await async_client.post("/students/", json=payload)
    assert response.status_code == 201
    data = response.json()

    for field in payload:
        assert field in data


async def test_invalid_email(async_client):
    payload = {
        "first_name": "Test",
        "last_name": "Bad",
        "email": "not-an-email",
        "phone": "206",
        "cohort_id": None
    }
    response = await async_client.post("/students/", json=payload)
    assert response.status_code == 422
