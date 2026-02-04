"""Tests for security headers middleware."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestSecurityHeaders:
    """Test security headers are present on responses."""

    def test_x_frame_options_header(self, client: TestClient):
        """Test X-Frame-Options header is present."""
        response = client.get("/health")
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_x_content_type_options_header(self, client: TestClient):
        """Test X-Content-Type-Options header is present."""
        response = client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_xss_protection_header(self, client: TestClient):
        """Test X-XSS-Protection header is present."""
        response = client.get("/health")
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_referrer_policy_header(self, client: TestClient):
        """Test Referrer-Policy header is present."""
        response = client.get("/health")
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_content_security_policy_header(self, client: TestClient):
        """Test Content-Security-Policy header is present."""
        response = client.get("/health")
        csp = response.headers.get("Content-Security-Policy")
        assert csp is not None
        assert "default-src 'self'" in csp
        assert "script-src" in csp

    def test_permissions_policy_header(self, client: TestClient):
        """Test Permissions-Policy header is present."""
        response = client.get("/health")
        pp = response.headers.get("Permissions-Policy")
        assert pp is not None
        assert "geolocation=()" in pp

    def test_headers_on_api_endpoints(self, client: TestClient):
        """Test security headers are present on API endpoints."""
        response = client.get("/api/v1/cohorts")
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_headers_on_404_response(self, client: TestClient):
        """Test security headers are present on 404 responses."""
        response = client.get("/nonexistent-page")
        assert response.status_code == 404
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_headers_on_static_files(self, client: TestClient):
        """Test security headers are present on static file responses."""
        response = client.get("/static/css/custom.css")
        # Static files may or may not exist, but headers should be there
        assert response.headers.get("X-Frame-Options") == "DENY"
