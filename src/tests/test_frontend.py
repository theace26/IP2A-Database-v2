"""
Frontend route tests.

Tests for HTML page rendering and static file serving.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


class TestPublicRoutes:
    """Tests for routes that don't require authentication."""

    def test_root_redirects_to_login(self):
        """Root path should redirect to login."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"

    def test_login_page_renders(self):
        """Login page should render with expected content."""
        response = client.get("/login")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "IBEW Local 46" in response.text
        assert "Log In" in response.text
        assert "Forgot password?" in response.text

    def test_forgot_password_page_renders(self):
        """Forgot password page should render."""
        response = client.get("/forgot-password")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Reset Password" in response.text


class TestProtectedRoutes:
    """Tests for routes that will require authentication.

    Note: These currently work without auth for Week 1.
    Week 2 will add auth requirements.
    """

    def test_dashboard_page_renders(self):
        """Dashboard page should render."""
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Dashboard" in response.text
        assert "Welcome back" in response.text

    def test_logout_redirects_to_login(self):
        """Logout should redirect to login."""
        response = client.get("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"


class TestStaticFiles:
    """Tests for static file serving."""

    def test_css_file_served(self):
        """Custom CSS should be accessible."""
        response = client.get("/static/css/custom.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]

    def test_js_file_served(self):
        """Custom JavaScript should be accessible."""
        response = client.get("/static/js/app.js")
        assert response.status_code == 200


class TestErrorPages:
    """Tests for custom error pages."""

    def test_404_for_unknown_page(self):
        """Unknown routes should return 404 HTML page."""
        response = client.get("/this-page-definitely-does-not-exist-xyz")
        assert response.status_code == 404
        assert "text/html" in response.headers["content-type"]
        assert "Page Not Found" in response.text

    def test_api_404_returns_json(self):
        """API routes should return JSON 404."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        assert "application/json" in response.headers["content-type"]


class TestPageContent:
    """Tests for specific page content."""

    def test_login_has_form(self):
        """Login page should have a form with required fields."""
        response = client.get("/login")
        assert 'name="email"' in response.text
        assert 'name="password"' in response.text
        assert 'hx-post="/api/auth/login"' in response.text

    def test_dashboard_has_stats_cards(self):
        """Dashboard should display stats cards."""
        response = client.get("/dashboard")
        assert "Total Members" in response.text
        assert "Students" in response.text
        assert "Open Grievances" in response.text
        assert "Dues MTD" in response.text

    def test_dashboard_has_quick_actions(self):
        """Dashboard should have quick action buttons."""
        response = client.get("/dashboard")
        assert "Quick Actions" in response.text
        assert "New Member" in response.text or "+ New Member" in response.text
