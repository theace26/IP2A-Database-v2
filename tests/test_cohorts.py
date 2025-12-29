async def test_create_cohort(async_client):
    payload = {
        "name": "Cohort A",
        "location_id": None,
        "start_date": "2024-01-01",
        "end_date": "2024-03-01",
        "primary_instructor_id": None
    }

    response = await async_client.post("/cohorts/", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Cohort A"
