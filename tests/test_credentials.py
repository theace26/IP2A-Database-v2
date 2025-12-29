from datetime import date

async def test_create_credential(async_client):
    # First create student
    student = await async_client.post("/students/", json={
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane@test.com",
        "phone": "123",
        "cohort_id": None
    })
    sid = student.json()["id"]

    payload = {
        "student_id": sid,
        "credential_name": "Forklift Certification",
        "date_awarded": str(date.today()),
        "attachment_path": None
    }

    response = await async_client.post("/credentials/", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["credential_name"] == "Forklift Certification"
    assert data["student_id"] == sid


async def test_credential_with_file(async_client):
    fake_pdf = io.BytesIO(b"%PDF test file")
    upload = await async_client.post(
        "/files/upload",
        files={"file": ("card.pdf", fake_pdf, "application/pdf")}
    )

    assert upload.status_code == 200
    file_path = upload.json()["file_path"]

    # Now create credential with file
    student = await async_client.post("/students/", json={
        "first_name": "Jack",
        "last_name": "Paper",
        "email": "jack@test.com",
        "phone": "123",
        "cohort_id": None
    })
    sid = student.json()["id"]

    response = await async_client.post("/credentials/", json={
        "student_id": sid,
        "credential_name": "OSHA 10",
        "date_awarded": str(date.today()),
        "attachment_path": file_path
    })

    assert response.status_code == 201
