from datetime import date
import uuid


async def test_record_hours(async_client):
    unique = str(uuid.uuid4())[:8]

    # Create instructor first
    instructor = await async_client.post(
        "/instructors/",
        json={
            "first_name": "Hours",
            "last_name": "Test",
            "email": f"hours_{unique}@test.com",
            "phone": "206-555-1111",
            "certification": "Journeyman",
        },
    )
    assert instructor.status_code in (200, 201)
    instructor_id = instructor.json()["id"]

    # Create location
    location = await async_client.post(
        "/locations/",
        json={
            "name": f"Test Location {unique}",
            "address": "456 Test Ave",
            "capacity": 20,
        },
    )
    assert location.status_code in (200, 201)
    location_id = location.json()["id"]

    payload = {
        "instructor_id": instructor_id,
        "location_id": location_id,
        "date": str(date.today()),
        "hours": 8.0,
        "notes": "Full day training",
    }

    response = await async_client.post("/instructor-hours/", json=payload)
    assert response.status_code in (200, 201)
