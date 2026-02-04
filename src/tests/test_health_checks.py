"""Tests for enhanced health check endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthChecks:
    """Test health check endpoints."""

    def test_basic_health_check(self, client: TestClient):
        """Test basic /health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_liveness_check(self, client: TestClient):
        """Test /health/live endpoint returns alive status."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data

    def test_readiness_check(self, client: TestClient):
        """Test /health/ready endpoint checks dependencies."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "checks" in data
        assert "database" in data["checks"]
        assert "version" in data
        assert "environment" in data
        assert "timestamp" in data

    def test_readiness_database_check(self, client: TestClient):
        """Test readiness check includes database status."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        db_check = data["checks"]["database"]
        assert db_check["status"] in ["healthy", "unhealthy"]

    def test_health_empty_endpoint(self, client: TestClient):
        """Test /health/ (with trailing slash) returns basic health."""
        response = client.get("/health/")
        # Should redirect or return the same as /health
        assert response.status_code in [200, 307]

    def test_metrics_endpoint(self, client: TestClient):
        """Test /health/metrics endpoint returns metrics."""
        response = client.get("/health/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ok", "error"]
        assert "timestamp" in data
        if data["status"] == "ok":
            assert "metrics" in data
            metrics = data["metrics"]
            assert "members_total" in metrics
            assert "users_total" in metrics
            assert "students_total" in metrics

    def test_health_response_format(self, client: TestClient):
        """Test health response follows expected JSON format."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_health_check_timestamp_format(self, client: TestClient):
        """Test health check timestamps are ISO 8601 format."""
        response = client.get("/health/ready")
        data = response.json()
        timestamp = data["timestamp"]
        # Should be ISO 8601 format (e.g., 2026-02-02T12:00:00+00:00)
        assert "T" in timestamp
        assert len(timestamp) > 10  # Minimum ISO date is 10 chars


class TestHealthCheckIntegration:
    """Integration tests for health checks with app state."""

    def test_health_during_request_processing(self, client: TestClient):
        """Test health checks work during normal request processing."""
        # Make a regular request first
        client.get("/api/v1/cohorts")
        # Then verify health is still good
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] in ["healthy", "degraded"]

    def test_concurrent_health_checks(self, client: TestClient):
        """Test multiple health checks can run concurrently."""
        import concurrent.futures

        def check_health():
            return client.get("/health/live")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(check_health) for _ in range(10)]
            results = [f.result() for f in futures]

        # All should succeed
        assert all(r.status_code == 200 for r in results)
