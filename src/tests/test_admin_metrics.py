"""Tests for admin metrics dashboard."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestAdminMetricsEndpoints:
    """Test admin metrics endpoints."""

    def test_metrics_dashboard_requires_auth(self, client: TestClient):
        """Test metrics dashboard redirects without auth."""
        response = client.get("/admin/metrics", follow_redirects=False)
        # Should redirect to login
        assert response.status_code in [302, 307]

    def test_metrics_api_requires_auth(self, client: TestClient):
        """Test metrics API endpoint requires authentication."""
        response = client.get("/admin/metrics/api")
        data = response.json()
        # Should indicate not authenticated
        assert "error" in data or response.status_code == 302

    def test_metrics_api_returns_json(self, client: TestClient):
        """Test metrics API returns JSON."""
        response = client.get("/admin/metrics/api")
        assert response.headers.get("content-type") == "application/json"


class TestBackupScripts:
    """Test backup script existence and structure."""

    def test_backup_script_exists(self):
        """Test backup_database.sh exists."""
        import os
        assert os.path.exists("/app/scripts/backup_database.sh")

    def test_verify_backup_script_exists(self):
        """Test verify_backup.sh exists."""
        import os
        assert os.path.exists("/app/scripts/verify_backup.sh")

    def test_archive_audit_script_exists(self):
        """Test archive_audit_logs.sh exists."""
        import os
        assert os.path.exists("/app/scripts/archive_audit_logs.sh")

    def test_cleanup_sessions_script_exists(self):
        """Test cleanup_sessions.sh exists."""
        import os
        assert os.path.exists("/app/scripts/cleanup_sessions.sh")

    def test_crontab_example_exists(self):
        """Test crontab.example exists."""
        import os
        assert os.path.exists("/app/scripts/crontab.example")


class TestRunbooks:
    """Test runbook documentation exists."""

    def test_runbooks_readme_exists(self):
        """Test runbooks README exists."""
        import os
        assert os.path.exists("/app/docs/runbooks/README.md")

    def test_incident_response_runbook_exists(self):
        """Test incident response runbook exists."""
        import os
        assert os.path.exists("/app/docs/runbooks/incident-response.md")

    def test_deployment_runbook_exists(self):
        """Test deployment runbook exists."""
        import os
        assert os.path.exists("/app/docs/runbooks/deployment.md")

    def test_backup_restore_runbook_exists(self):
        """Test backup-restore runbook exists."""
        import os
        assert os.path.exists("/app/docs/runbooks/backup-restore.md")

    def test_disaster_recovery_runbook_exists(self):
        """Test disaster-recovery runbook exists."""
        import os
        assert os.path.exists("/app/docs/runbooks/disaster-recovery.md")
