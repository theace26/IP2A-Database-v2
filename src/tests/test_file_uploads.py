import io
import os

async def test_upload_pdf(async_client):
    fake_pdf = io.BytesIO(b"%PDF-1.4 test pdf data")
    
    response = await async_client.post(
        "/files/upload",
        files={"file": ("test.pdf", fake_pdf, "application/pdf")}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["file_name"].endswith(".pdf")
    assert os.path.exists(data["file_path"])
    assert data["content_type"] == "application/pdf"


async def test_upload_jpeg(async_client):
    fake_img = io.BytesIO(b"\xff\xd8\xff test jpeg data")

    response = await async_client.post(
        "/files/upload",
        files={"file": ("photo.jpg", fake_img, "image/jpeg")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["file_name"].endswith(".jpg")
    assert os.path.exists(data["file_path"])


async def test_reject_invalid_type(async_client):
    fake_exe = io.BytesIO(b"MZ... binary exe")

    response = await async_client.post(
        "/files/upload",
        files={"file": ("malware.exe", fake_exe, "application/x-msdownload")}
    )

    # Expecting failure once validation rules are added
    assert response.status_code in (400, 415)
