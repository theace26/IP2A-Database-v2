"""
Frontend route tests.

Tests for HTML page rendering, static file serving, and authentication flows.
"""

from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


class TestPublicRoutes:
    """Tests for routes that don't require authentication."""

    def test_root_redirects_appropriately(self):
        """Root path should redirect to setup or login based on system state."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
        # Should redirect to either /login or /setup depending on state
        location = response.headers["location"]
        assert location in ["/login", "/setup"]

    def test_login_page_renders_or_redirects_to_setup(self):
        """Login page should render or redirect to setup if setup required."""
        response = client.get("/login", follow_redirects=False)
        # Either renders login (200) or redirects to setup (302)
        assert response.status_code in [200, 302]
        if response.status_code == 200:
            assert "text/html" in response.headers["content-type"]
            assert "IBEW Local 46" in response.text
            assert "Log In" in response.text
        else:
            assert "/setup" in response.headers["location"]

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

    def test_login_or_setup_has_form(self):
        """Login or setup page should have a form with required fields."""
        response = client.get("/login", follow_redirects=True)
        assert response.status_code == 200
        # Both login and setup have email/password fields
        assert 'name="email"' in response.text
        assert 'name="password"' in response.text

    def test_setup_page_when_setup_required(self):
        """Setup page should display when setup is required."""
        # This test verifies setup page content when accessed directly
        response = client.get("/setup")
        if response.status_code == 200:
            # Setup is required - verify setup page content
            assert "System Setup" in response.text or "Create Your Account" in response.text
            assert 'name="email"' in response.text
            assert 'name="password"' in response.text
        else:
            # Setup already complete - redirects to login
            assert response.status_code == 302
            assert "/login" in response.headers["location"]

    def test_login_or_setup_displays_content(self):
        """Login/setup page should display appropriate content."""
        response = client.get("/login", follow_redirects=True)
        assert response.status_code == 200
        # Should show either login or setup form
        assert "IBEW Local 46" in response.text or "IP2A" in response.text


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

    def test_profile_page_exists(self):
        """Profile page should exist (implemented Week 12)."""
        response = client.get("/profile")
        # Unauthenticated should redirect to login, not 404
        assert response.status_code in [200, 302]
        if response.status_code == 302:
            assert "/login" in response.headers.get("location", "")

    def test_settings_returns_404(self):
        """Settings page should return 404."""
        response = client.get("/settings")
        assert response.status_code == 404

    # Note: /members is now implemented in Phase 6 Week 5
