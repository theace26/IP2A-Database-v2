from datetime import date
import uuid


async def test_submit_application(async_client):
    unique = str(uuid.uuid4())[:8]
    student = await async_client.post(
        "/students/",
        json={
            "first_name": "JATC",
            "last_name": "Applicant",
            "email": f"jatc_{unique}@test.com",
            "phone": "206-555-3333",
            "cohort_id": None,
        },
    )
    assert student.status_code in (200, 201)
    student_id = student.json()["id"]

    payload = {
        "student_id": student_id,
        "application_date": str(date.today()),
        "status": "pending",
    }

    response = await async_client.post("/jatc-applications/", json=payload)
    assert response.status_code in (200, 201)
