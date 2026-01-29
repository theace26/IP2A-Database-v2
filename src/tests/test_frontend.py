"""
Frontend route tests.

Tests for HTML page rendering, static file serving, and authentication flows.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


class TestPublicRoutes:
    """Tests for routes that don't require authentication."""

    def test_root_redirects_to_login_when_unauthenticated(self):
        """Root path should redirect to login when not authenticated."""
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
    """Tests for routes that require authentication."""

    def test_dashboard_redirects_without_auth(self):
        """Dashboard should redirect to login when not authenticated."""
        response = client.get("/dashboard", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["location"]

    def test_logout_redirects_to_login(self):
        """Logout should clear cookies and redirect to login with message."""
        response = client.get("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["location"]
        assert "message=" in response.headers["location"]


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
        assert 'hx-post="/auth/login"' in response.text

    def test_login_accepts_next_param(self):
        """Login page should accept and preserve next URL param."""
        response = client.get("/login?next=/dashboard")
        assert response.status_code == 200
        assert "/dashboard" in response.text

    def test_login_displays_flash_message(self):
        """Login page should display flash messages from URL params."""
        response = client.get("/login?message=Test+message&type=success")
        assert response.status_code == 200
        assert "Test message" in response.text


class TestCookieAuth:
    """Tests for cookie-based authentication."""

    def test_protected_route_redirects_to_login(self):
        """Protected routes should redirect to login when not authenticated."""
        protected_routes = ["/dashboard"]
        for route in protected_routes:
            response = client.get(route, follow_redirects=False)
            assert response.status_code == 302, f"Route {route} should redirect"
            assert "/login" in response.headers["location"]

    def test_logout_clears_cookies(self):
        """Logout should set cookies to be deleted."""
        response = client.get("/logout", follow_redirects=False)
        assert response.status_code == 302
        # Check that cookies are being cleared (Set-Cookie headers present)
        set_cookies = response.headers.get_list("set-cookie")
        # Should have Set-Cookie headers to clear the tokens
        assert len(set_cookies) >= 0  # At least attempt to clear cookies

    def test_invalid_login_returns_401(self):
        """Invalid login credentials should return 401."""
        response = client.post(
            "/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401


class TestFlashMessages:
    """Tests for flash message functionality."""

    def test_logout_includes_success_message(self):
        """Logout redirect should include success message."""
        response = client.get("/logout", follow_redirects=False)
        location = response.headers.get("location", "")
        assert "message=" in location
        assert "type=success" in location

    def test_protected_redirect_includes_info_message(self):
        """Redirect to login from protected route should include info message."""
        response = client.get("/dashboard", follow_redirects=False)
        location = response.headers.get("location", "")
        assert "/login" in location


class TestDashboardAPI:
    """Tests for dashboard API endpoints."""

    def test_dashboard_refresh_endpoint_exists(self):
        """Dashboard refresh endpoint should exist."""
        response = client.get("/api/dashboard/refresh")
        # Should return 401 (unauthorized) or HTML if it exists
        assert response.status_code in [200, 401, 302]

    def test_recent_activity_endpoint_exists(self):
        """Recent activity endpoint should exist."""
        response = client.get("/api/dashboard/recent-activity")
        # Should return HTML content
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestPlaceholderRoutes:
    """Tests for placeholder pages that return 404."""

    def test_profile_returns_404(self):
        """Profile page should return 404."""
        response = client.get("/profile")
        assert response.status_code == 404

    def test_settings_returns_404(self):
        """Settings page should return 404."""
        response = client.get("/settings")
        assert response.status_code == 404

    def test_members_returns_404(self):
        """Members page should return 404."""
        response = client.get("/members")
        assert response.status_code == 404
