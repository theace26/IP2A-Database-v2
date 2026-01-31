"""Tests for Document Management endpoints (Phase 3)."""

import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

from src.tests.helpers import create_member


class MockS3Service:
    """Mock S3 service for testing without actual MinIO."""

    def __init__(self):
        self.files = {}
        self.bucket_exists = True

    def ensure_bucket_exists(self):
        return self.bucket_exists

    def upload_file(self, file_data, object_key, content_type=None, metadata=None):
        content = file_data.read()
        self.files[object_key] = {
            "content": content,
            "content_type": content_type,
            "metadata": metadata,
            "size": len(content),
        }
        return True

    def download_file(self, object_key):
        if object_key not in self.files:
            return None
        return BytesIO(self.files[object_key]["content"])

    def get_presigned_url(self, object_key, expiry=None, download=False, filename=None):
        if object_key not in self.files:
            return None
        return f"http://minio:9000/test-bucket/{object_key}?presigned=true"

    def get_upload_presigned_url(self, object_key, content_type=None, expiry=None):
        return f"http://minio:9000/test-bucket/{object_key}?upload=true"

    def delete_file(self, object_key):
        if object_key in self.files:
            del self.files[object_key]
            return True
        return False

    def get_file_metadata(self, object_key):
        if object_key not in self.files:
            return None
        return {
            "size": self.files[object_key]["size"],
            "content_type": self.files[object_key]["content_type"],
            "last_modified": "2026-01-28T00:00:00Z",
        }


@pytest.fixture
def mock_s3():
    """Fixture to mock S3 service."""
    mock = MockS3Service()
    with patch("src.services.document_service.get_s3_service", return_value=mock):
        yield mock


async def test_upload_document(async_client, mock_s3):
    """Test uploading a document via API."""
    # Create a member first
    member = await create_member(async_client)

    # Create a test file
    file_content = b"This is a test PDF content"
    files = {"file": ("test_document.pdf", BytesIO(file_content), "application/pdf")}
    data = {
        "record_type": "member",
        "record_id": member["id"],
        "category": "certifications",
    }

    response = await async_client.post("/documents/upload", files=files, data=data)
    assert response.status_code == 201, f"Upload failed: {response.json()}"

    result = response.json()
    assert result["original_filename"] == "test_document.pdf"
    assert result["content_type"] == "application/pdf"
    assert result["record_type"] == "member"
    assert result["record_id"] == member["id"]
    assert result["category"] == "certifications"
    assert "id" in result
    assert "s3_key" in result


async def test_upload_document_invalid_extension(async_client, mock_s3):
    """Test uploading a document with disallowed extension."""
    member = await create_member(async_client)

    file_content = b"Malicious executable content"
    files = {"file": ("malware.exe", BytesIO(file_content), "application/octet-stream")}
    data = {
        "record_type": "member",
        "record_id": member["id"],
    }

    response = await async_client.post("/documents/upload", files=files, data=data)
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]


async def test_get_document(async_client, mock_s3):
    """Test getting document metadata by ID."""
    # Upload a document first
    member = await create_member(async_client)
    file_content = b"Test document content"
    files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
    data = {"record_type": "member", "record_id": member["id"]}

    upload_response = await async_client.post("/documents/upload", files=files, data=data)
    assert upload_response.status_code == 201
    doc_id = upload_response.json()["id"]

    # Get document
    response = await async_client.get(f"/documents/{doc_id}")
    assert response.status_code == 200

    result = response.json()
    assert result["id"] == doc_id
    assert result["original_filename"] == "test.pdf"
    assert result["is_deleted"] is False


async def test_get_document_not_found(async_client, mock_s3):
    """Test getting a non-existent document."""
    response = await async_client.get("/documents/99999")
    assert response.status_code == 404


async def test_get_download_url(async_client, mock_s3):
    """Test getting a presigned download URL."""
    # Upload a document first
    member = await create_member(async_client)
    file_content = b"Test document for download"
    files = {"file": ("download_test.pdf", BytesIO(file_content), "application/pdf")}
    data = {"record_type": "member", "record_id": member["id"]}

    upload_response = await async_client.post("/documents/upload", files=files, data=data)
    assert upload_response.status_code == 201
    doc_id = upload_response.json()["id"]

    # Get download URL
    response = await async_client.get(f"/documents/{doc_id}/download-url")
    assert response.status_code == 200

    result = response.json()
    assert "download_url" in result
    assert result["expires_in"] == 3600  # Default expiry


async def test_list_documents(async_client, mock_s3):
    """Test listing documents."""
    response = await async_client.get("/documents/")
    assert response.status_code == 200

    result = response.json()
    assert "documents" in result
    assert "total" in result
    assert "page" in result
    assert "page_size" in result
    assert isinstance(result["documents"], list)


async def test_list_documents_with_filters(async_client, mock_s3):
    """Test listing documents with filters."""
    # Upload a document
    member = await create_member(async_client)
    file_content = b"Test document"
    files = {"file": ("filtered.pdf", BytesIO(file_content), "application/pdf")}
    data = {"record_type": "member", "record_id": member["id"], "category": "dues"}

    upload_response = await async_client.post("/documents/upload", files=files, data=data)
    assert upload_response.status_code == 201

    # List with filters
    response = await async_client.get(
        f"/documents/?record_type=member&record_id={member['id']}&category=dues"
    )
    assert response.status_code == 200

    result = response.json()
    assert result["total"] >= 1
    for doc in result["documents"]:
        assert doc["record_type"] == "member"
        assert doc["record_id"] == member["id"]


async def test_delete_document_soft(async_client, mock_s3):
    """Test soft deleting a document."""
    # Upload a document
    member = await create_member(async_client)
    file_content = b"Document to delete"
    files = {"file": ("delete_me.pdf", BytesIO(file_content), "application/pdf")}
    data = {"record_type": "member", "record_id": member["id"]}

    upload_response = await async_client.post("/documents/upload", files=files, data=data)
    assert upload_response.status_code == 201
    doc_id = upload_response.json()["id"]

    # Soft delete
    response = await async_client.delete(f"/documents/{doc_id}")
    assert response.status_code == 200
    assert response.json()["hard_delete"] is False

    # Document should not be found (soft deleted)
    get_response = await async_client.get(f"/documents/{doc_id}")
    assert get_response.status_code == 404


async def test_delete_document_hard(async_client, mock_s3):
    """Test hard deleting a document."""
    # Upload a document
    member = await create_member(async_client)
    file_content = b"Document to hard delete"
    files = {"file": ("hard_delete.pdf", BytesIO(file_content), "application/pdf")}
    data = {"record_type": "member", "record_id": member["id"]}

    upload_response = await async_client.post("/documents/upload", files=files, data=data)
    assert upload_response.status_code == 201
    doc_id = upload_response.json()["id"]

    # Hard delete
    response = await async_client.delete(f"/documents/{doc_id}?hard_delete=true")
    assert response.status_code == 200
    assert response.json()["hard_delete"] is True


async def test_presigned_upload_url(async_client, mock_s3):
    """Test getting a presigned upload URL."""
    member = await create_member(async_client)

    payload = {
        "filename": "large_file.pdf",
        "content_type": "application/pdf",
        "record_type": "member",
        "record_id": member["id"],
        "category": "grievances",
    }

    response = await async_client.post("/documents/presigned-upload", json=payload)
    assert response.status_code == 200

    result = response.json()
    assert "upload_url" in result
    assert "s3_key" in result
    assert "expires_in" in result


async def test_presigned_upload_invalid_extension(async_client, mock_s3):
    """Test presigned upload rejects invalid extensions."""
    member = await create_member(async_client)

    payload = {
        "filename": "script.sh",
        "content_type": "text/x-shellscript",
        "record_type": "member",
        "record_id": member["id"],
    }

    response = await async_client.post("/documents/presigned-upload", json=payload)
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]
