async def test_create_location(async_client):
    payload = {
        "name": "Seattle Training Center",
        "address": "123 Main St, Seattle, WA 98101",
        "capacity": 30,
    }
    response = await async_client.post("/locations/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["address"] == payload["address"]
    assert data["capacity"] == payload["capacity"]


async def test_missing_required_field(async_client):
    # Missing 'name' should fail validation
    response = await async_client.post("/locations/", json={"address": "123 Main St"})
    assert response.status_code == 422  # FastAPI validation error


async def test_list_locations(async_client):
    response = await async_client.get("/locations/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
