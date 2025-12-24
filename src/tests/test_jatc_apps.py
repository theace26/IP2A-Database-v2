async def test_submit_application(async_client):
    # Create student
    s = await async_client.post("/students/", json={
        "first_name": "App",
        "last_name": "User",
        "email": "app@test.com",
        "phone": "123",
        "cohort_id": None
    })
    sid = s.json()["id"]

    payload = {
        "student_id": sid,
        "status": "submitted",
        "site_preference": "Seattle",
        "submitted_date": "2024-02-01",
        "supporting_docs_path": None
    }

    response = await async_client.post("/jatc-apps/", json=payload)
    assert response.status_code == 201
    assert response.json()["status"] == "submitted"
