from datetime import date
import uuid


async def test_issue_tool(async_client):
    unique = str(uuid.uuid4())[:8]
    student = await async_client.post(
        "/students/",
        json={
            "first_name": "Tool",
            "last_name": "User",
            "email": f"tool_{unique}@test.com",
            "phone": "206-555-2222",
            "cohort_id": None,
        },
    )
    assert student.status_code in (200, 201)
    student_id = student.json()["id"]

    payload = {
        "student_id": student_id,
        "tool_name": "Multimeter",
        "quantity": 1,
        "date_issued": str(date.today()),
    }

    response = await async_client.post("/tools/", json=payload)
    assert response.status_code in (200, 201)
