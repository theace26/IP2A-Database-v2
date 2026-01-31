from datetime import date
import uuid


async def test_create_credential(async_client):
    unique = str(uuid.uuid4())[:8]
    student = await async_client.post(
        "/students/",
        json={
            "first_name": "Jane",
            "last_name": "Smith",
            "email": f"jane_{unique}@test.com",
            "phone": "123-456-7890",
            "cohort_id": None,
        },
    )
    assert student.status_code in (
        200,
        201,
    ), f"Student creation failed: {student.json()}"
    sid = student.json()["id"]

    payload = {
        "student_id": sid,
        "credential_name": "Forklift Certification",
        "issue_date": str(date.today()),
    }

    response = await async_client.post("/credentials/", json=payload)
    assert response.status_code in (
        200,
        201,
    ), f"Credential creation failed: {response.json()}"


async def test_credential_with_file(async_client):
    unique = str(uuid.uuid4())[:8]
    student = await async_client.post(
        "/students/",
        json={
            "first_name": "Jack",
            "last_name": "Paper",
            "email": f"jack_{unique}@test.com",
            "phone": "123-456-7890",
            "cohort_id": None,
        },
    )
    assert student.status_code in (200, 201)
    sid = student.json()["id"]

    response = await async_client.post(
        "/credentials/",
        json={
            "student_id": sid,
            "credential_name": "OSHA 10",
            "issue_date": str(date.today()),
        },
    )
    assert response.status_code in (200, 201)
