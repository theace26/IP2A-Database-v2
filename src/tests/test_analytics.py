"""Tests for analytics dashboard and report builder."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestAnalyticsService:
    """Test AnalyticsService methods."""

    def test_membership_stats_returns_dict(self):
        """Test membership stats returns expected structure."""
        from src.services.analytics_service import AnalyticsService
        from src.db.session import get_db

        db = next(get_db())
        service = AnalyticsService(db)
        stats = service.get_membership_stats()

        assert isinstance(stats, dict)
        assert "total" in stats
        assert "active" in stats
        assert "inactive" in stats
        assert "new_this_month" in stats
        assert "retention_rate" in stats

    def test_membership_trend_returns_list(self):
        """Test membership trend returns list with expected months."""
        from src.services.analytics_service import AnalyticsService
        from src.db.session import get_db

        db = next(get_db())
        service = AnalyticsService(db)
        trend = service.get_membership_trend(months=6)

        assert isinstance(trend, list)
        assert len(trend) == 6
        for item in trend:
            assert "month" in item
            assert "label" in item
            assert "count" in item

    def test_dues_analytics_returns_dict(self):
        """Test dues analytics returns expected structure."""
        from src.services.analytics_service import AnalyticsService
        from src.db.session import get_db

        db = next(get_db())
        service = AnalyticsService(db)
        dues = service.get_dues_analytics()

        assert isinstance(dues, dict)
        assert "total_collected" in dues
        assert "payment_count" in dues
        assert "average_payment" in dues
        assert "payment_methods" in dues
        assert isinstance(dues["payment_methods"], list)

    def test_delinquency_report_returns_dict(self):
        """Test delinquency report returns expected structure."""
        from src.services.analytics_service import AnalyticsService
        from src.db.session import get_db

        db = next(get_db())
        service = AnalyticsService(db)
        report = service.get_delinquency_report()

        assert isinstance(report, dict)
        assert "overdue_count" in report
        assert "members" in report

    def test_training_metrics_returns_dict(self):
        """Test training metrics returns expected structure."""
        from src.services.analytics_service import AnalyticsService
        from src.db.session import get_db

        db = next(get_db())
        service = AnalyticsService(db)
        metrics = service.get_training_metrics()

        assert isinstance(metrics, dict)
        assert "total_students" in metrics
        assert "active" in metrics
        assert "completed" in metrics
        assert "completion_rate" in metrics

    def test_activity_metrics_returns_dict(self):
        """Test activity metrics returns expected structure."""
        from src.services.analytics_service import AnalyticsService
        from src.db.session import get_db

        db = next(get_db())
        service = AnalyticsService(db)
        activity = service.get_activity_metrics(days=7)

        assert isinstance(activity, dict)
        assert "period_days" in activity
        assert activity["period_days"] == 7
        assert "action_breakdown" in activity
        assert "total_actions" in activity
        assert "daily_activity" in activity


class TestReportBuilderService:
    """Test ReportBuilderService methods."""

    def test_get_available_entities(self):
        """Test getting available entities for reports."""
        from src.services.report_builder_service import ReportBuilderService
        from src.db.session import get_db

        db = next(get_db())
        service = ReportBuilderService(db)
        entities = service.get_available_entities()

        assert isinstance(entities, list)
        assert len(entities) > 0
        for entity in entities:
            assert "key" in entity
            assert "label" in entity
            assert "fields" in entity

    def test_build_members_report(self):
        """Test building a members report."""
        from src.services.report_builder_service import ReportBuilderService
        from src.db.session import get_db

        db = next(get_db())
        service = ReportBuilderService(db)
        report = service.build_report(
            entity="members",
            fields=["id", "first_name", "last_name"],
            limit=10,
        )

        assert isinstance(report, dict)
        assert report["entity"] == "members"
        assert report["fields"] == ["id", "first_name", "last_name"]
        assert "data" in report
        assert "count" in report
        assert "generated_at" in report

    def test_build_report_invalid_entity_raises(self):
        """Test that invalid entity raises ValueError."""
        from src.services.report_builder_service import ReportBuilderService
        from src.db.session import get_db

        db = next(get_db())
        service = ReportBuilderService(db)

        with pytest.raises(ValueError, match="Unknown entity"):
            service.build_report(entity="invalid", fields=["id"])

    def test_export_to_csv(self):
        """Test exporting report to CSV."""
        from src.services.report_builder_service import ReportBuilderService
        from src.db.session import get_db

        db = next(get_db())
        service = ReportBuilderService(db)
        report = service.build_report(entity="members", fields=["id", "first_name"], limit=5)
        csv_content = service.export_to_csv(report)

        assert isinstance(csv_content, str)
        assert "id,first_name" in csv_content

    def test_export_to_excel(self):
        """Test exporting report to Excel."""
        from src.services.report_builder_service import ReportBuilderService
        from src.db.session import get_db

        db = next(get_db())
        service = ReportBuilderService(db)
        report = service.build_report(entity="members", fields=["id", "first_name"], limit=5)
        excel_content = service.export_to_excel(report)

        assert isinstance(excel_content, bytes)
        # Excel files start with PK (zip signature)
        assert excel_content[:2] == b"PK"


class TestAnalyticsEndpoints:
    """Test analytics dashboard endpoints."""

    def test_analytics_dashboard_requires_auth(self, client: TestClient):
        """Test analytics dashboard redirects to login without auth."""
        response = client.get("/analytics", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers.get("location", "")

    def test_membership_analytics_requires_auth(self, client: TestClient):
        """Test membership analytics redirects to login without auth."""
        response = client.get("/analytics/membership", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers.get("location", "")

    def test_dues_analytics_requires_auth(self, client: TestClient):
        """Test dues analytics redirects to login without auth."""
        response = client.get("/analytics/dues", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers.get("location", "")

    def test_report_builder_requires_auth(self, client: TestClient):
        """Test report builder redirects to login without auth."""
        response = client.get("/analytics/builder", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers.get("location", "")


class TestAnalyticsTemplates:
    """Test analytics template files exist."""

    def test_dashboard_template_exists(self):
        """Test dashboard template exists."""
        import os

        assert os.path.exists("/app/src/templates/analytics/dashboard.html")

    def test_membership_template_exists(self):
        """Test membership template exists."""
        import os

        assert os.path.exists("/app/src/templates/analytics/membership.html")

    def test_dues_template_exists(self):
        """Test dues template exists."""
        import os

        assert os.path.exists("/app/src/templates/analytics/dues.html")

    def test_builder_template_exists(self):
        """Test builder template exists."""
        import os

        assert os.path.exists("/app/src/templates/analytics/builder.html")
