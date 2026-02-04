"""Tests for mobile optimization and PWA features."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestMobileEndpoints:
    """Test mobile-specific endpoints."""

    def test_offline_page_renders(self, client: TestClient):
        """Test offline page renders correctly."""
        response = client.get("/offline")
        assert response.status_code == 200
        assert "You're Offline" in response.text or "offline" in response.text.lower()

    def test_manifest_served(self, client: TestClient):
        """Test PWA manifest is served."""
        response = client.get("/static/manifest.json")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_manifest_content(self, client: TestClient):
        """Test PWA manifest has required fields."""
        response = client.get("/static/manifest.json")
        data = response.json()
        assert "name" in data
        assert "short_name" in data
        assert "start_url" in data
        assert "display" in data
        assert "icons" in data

    def test_service_worker_served(self, client: TestClient):
        """Test service worker file is served."""
        response = client.get("/static/sw.js")
        assert response.status_code == 200
        assert "CACHE_NAME" in response.text or "serviceWorker" in response.text


class TestMobileCSS:
    """Test mobile CSS assets."""

    def test_mobile_css_exists(self):
        """Test mobile.css exists."""
        import os
        assert os.path.exists("/app/src/static/css/mobile.css")

    def test_mobile_css_served(self, client: TestClient):
        """Test mobile.css is served."""
        response = client.get("/static/css/mobile.css")
        assert response.status_code == 200
        assert "text/css" in response.headers.get("content-type", "")


class TestMobileTemplates:
    """Test mobile template components."""

    def test_mobile_drawer_exists(self):
        """Test mobile drawer template exists."""
        import os
        assert os.path.exists("/app/src/templates/components/_mobile_drawer.html")

    def test_bottom_nav_exists(self):
        """Test bottom navigation template exists."""
        import os
        assert os.path.exists("/app/src/templates/components/_bottom_nav.html")

    def test_offline_template_exists(self):
        """Test offline template exists."""
        import os
        assert os.path.exists("/app/src/templates/offline.html")


class TestPWAMeta:
    """Test PWA meta tags in base template."""

    def test_base_template_has_manifest(self):
        """Test base template includes manifest link."""
        with open("/app/src/templates/base.html") as f:
            content = f.read()
            assert "manifest.json" in content

    def test_base_template_has_theme_color(self):
        """Test base template includes theme-color meta."""
        with open("/app/src/templates/base.html") as f:
            content = f.read()
            assert "theme-color" in content

    def test_base_template_has_apple_meta(self):
        """Test base template includes Apple PWA meta tags."""
        with open("/app/src/templates/base.html") as f:
            content = f.read()
            assert "apple-mobile-web-app-capable" in content

    def test_base_template_has_service_worker(self):
        """Test base template includes service worker registration."""
        with open("/app/src/templates/base.html") as f:
            content = f.read()
            assert "serviceWorker" in content

    def test_base_template_has_mobile_css(self):
        """Test base template includes mobile.css."""
        with open("/app/src/templates/base.html") as f:
            content = f.read()
            assert "mobile.css" in content
