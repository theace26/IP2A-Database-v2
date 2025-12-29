async def test_create_location(async_client):
    payload = {
        "name": "Seattle Campus",
        "address": "123 Main St",
        "city": "Seattle",
        "state": "WA",
        "zip_code": "98101"
    }

    response = await async_client.post("/locations/", json=payload)
    assert response.status_code == 201
    data = response.json()

    for field in payload:
        assert data[field] == payload[field]


async def test_missing_required_field(async_client):
    response = await async_client.post("/locations/", json={"city": "Seattle"})
    assert response.status_code == 422  # FastAPI validation error


async def test_list_locations(async_client):
    response = await async_client.get("/locations/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
