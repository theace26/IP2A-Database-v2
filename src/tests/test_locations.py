async def test_create_location(async_client):
    payload = {
        "name": "Training Center A",
        "address": "123 Main St",
        "city": "Seattle",
        "state": "WA",
        "capacity": 30,
    }

    response = await async_client.post("/locations/", json=payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["name"] == "Training Center A"


async def test_missing_required_field(async_client):
    payload = {"address": "123 Main St"}
    response = await async_client.post("/locations/", json=payload)
    assert response.status_code == 422


async def test_list_locations(async_client):
    response = await async_client.get("/locations/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
