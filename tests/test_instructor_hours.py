async def test_record_hours(async_client):
    # create instructor
    inst = await async_client.post("/instructors/", json={
        "first_name": "A",
        "last_name": "B",
        "email": "x@y.com"
    })
    iid = inst.json()["id"]

    # create location
    loc = await async_client.post("/locations/", json={
        "name": "HQ",
        "address": "123 St",
        "city": "Seattle",
        "state": "WA",
        "zip_code": "98101"
    })
    lid = loc.json()["id"]

    payload = {
        "instructor_id": iid,
        "location_id": lid,
        "hours": 8.0,
        "date": "2024-02-01",
        "cohort_id": None
    }

    response = await async_client.post("/instructor-hours/", json=payload)
    assert response.status_code == 201
    assert response.json()["hours"] == 8.0
