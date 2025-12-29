async def test_issue_tool(async_client):
    # Create student
    s = await async_client.post("/students/", json={
        "first_name": "Tool",
        "last_name": "User",
        "email": "tool@ibew.com",
        "phone": "123",
        "cohort_id": None
    })
    sid = s.json()["id"]

    payload = {
        "student_id": sid,
        "tool_name": "Voltage Tester",
        "date_issued": "2024-01-10",
        "receipt_path": None
    }

    response = await async_client.post("/tools/", json=payload)
    assert response.status_code == 201
    assert response.json()["tool_name"] == "Voltage Tester"
