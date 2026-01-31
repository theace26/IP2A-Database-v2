from datetime import date, timedelta


async def test_create_cohort(async_client):
    payload = {
        "name": "Cohort 2025-A",
        "description": "Spring 2025 class",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=90)),
    }

    response = await async_client.post("/cohorts/", json=payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["name"] == "Cohort 2025-A"
