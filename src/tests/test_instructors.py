async def test_create_instructor(async_client):
    payload = {
        "first_name": "Alice",
        "last_name": "Johnson",
        "email": "alice@ibew.org"
    }

    response = await async_client.post("/instructors/", json=payload)
    assert response.status_code == 201
    data = response.json()

    for field in payload:
        assert data[field] == payload[field]


async def test_instructor_list(async_client):
    response = await async_client.get("/instructors/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
