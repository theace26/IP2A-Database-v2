"""Tests for AuditLogs endpoints (read-only)."""


async def test_list_audit_logs(async_client):
    """Test listing all audit logs."""
    response = await async_client.get("/audit-logs/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_get_nonexistent_audit_log(async_client):
    """Test getting a non-existent audit log returns 404."""
    response = await async_client.get("/audit-logs/999999")
    assert response.status_code == 404


async def test_list_audit_logs_by_table(async_client):
    """Test listing audit logs for a specific table."""
    response = await async_client.get("/audit-logs/by-table/members")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # If there are any results, verify they're for the correct table
    for log in data:
        assert log["table_name"] == "members"


async def test_list_audit_logs_by_record(async_client):
    """Test listing audit logs for a specific record."""
    # Use a generic test - we may not have specific records
    response = await async_client.get("/audit-logs/by-record/organizations/1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # If there are any results, verify they're for the correct record
    for log in data:
        assert log["table_name"] == "organizations"
        assert log["record_id"] == "1"


async def test_audit_logs_pagination(async_client):
    """Test pagination for audit logs."""
    # Test with different skip/limit values
    response = await async_client.get("/audit-logs/?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10
