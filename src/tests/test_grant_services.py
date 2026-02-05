"""Tests for grant services."""

from src.services.grant_metrics_service import GrantMetricsService
from src.services.grant_report_service import GrantReportService
from src.db.enums import GrantStatus, GrantEnrollmentStatus, GrantOutcome


class TestGrantMetricsService:
    """Test GrantMetricsService."""

    def test_service_imports(self):
        """Verify GrantMetricsService can be imported."""
        assert GrantMetricsService is not None

    def test_status_badge_class(self):
        """Test status badge class helper."""
        assert (
            GrantMetricsService.get_status_badge_class(GrantStatus.PENDING)
            == "badge-warning"
        )
        assert (
            GrantMetricsService.get_status_badge_class(GrantStatus.ACTIVE)
            == "badge-success"
        )
        assert (
            GrantMetricsService.get_status_badge_class(GrantStatus.COMPLETED)
            == "badge-info"
        )
        assert (
            GrantMetricsService.get_status_badge_class(GrantStatus.CLOSED)
            == "badge-ghost"
        )
        assert (
            GrantMetricsService.get_status_badge_class(GrantStatus.SUSPENDED)
            == "badge-error"
        )

    def test_enrollment_status_badge_class(self):
        """Test enrollment status badge class helper."""
        assert (
            GrantMetricsService.get_enrollment_status_badge_class(
                GrantEnrollmentStatus.ENROLLED
            )
            == "badge-info"
        )
        assert (
            GrantMetricsService.get_enrollment_status_badge_class(
                GrantEnrollmentStatus.ACTIVE
            )
            == "badge-success"
        )
        assert (
            GrantMetricsService.get_enrollment_status_badge_class(
                GrantEnrollmentStatus.COMPLETED
            )
            == "badge-primary"
        )
        assert (
            GrantMetricsService.get_enrollment_status_badge_class(
                GrantEnrollmentStatus.WITHDRAWN
            )
            == "badge-warning"
        )
        assert (
            GrantMetricsService.get_enrollment_status_badge_class(
                GrantEnrollmentStatus.DROPPED
            )
            == "badge-error"
        )

    def test_outcome_badge_class(self):
        """Test outcome badge class helper."""
        assert (
            GrantMetricsService.get_outcome_badge_class(GrantOutcome.COMPLETED_PROGRAM)
            == "badge-success"
        )
        assert (
            GrantMetricsService.get_outcome_badge_class(
                GrantOutcome.ENTERED_APPRENTICESHIP
            )
            == "badge-primary"
        )
        assert (
            GrantMetricsService.get_outcome_badge_class(
                GrantOutcome.OBTAINED_EMPLOYMENT
            )
            == "badge-primary"
        )
        assert (
            GrantMetricsService.get_outcome_badge_class(GrantOutcome.WITHDRAWN)
            == "badge-warning"
        )


class TestGrantReportService:
    """Test GrantReportService."""

    def test_service_imports(self):
        """Verify GrantReportService can be imported."""
        assert GrantReportService is not None

    def test_report_service_has_generate_methods(self):
        """Verify GrantReportService has expected methods."""
        assert hasattr(GrantReportService, "generate_report")
        assert hasattr(GrantReportService, "generate_excel_report")


class TestGrantFrontendRouter:
    """Test grants frontend router."""

    def test_router_imports(self):
        """Verify grants frontend router can be imported."""
        from src.routers.grants_frontend import router

        assert router is not None

    def test_router_has_routes(self):
        """Verify router has expected routes."""
        from src.routers.grants_frontend import router

        # Get route paths
        paths = [route.path for route in router.routes]

        # Check expected routes exist
        assert "/grants" in paths  # Landing page
        assert "/grants/list" in paths  # List page
        assert "/grants/{grant_id}" in paths  # Detail page
        assert "/grants/{grant_id}/enrollments" in paths
        assert "/grants/{grant_id}/expenses" in paths
        assert "/grants/{grant_id}/reports" in paths
        assert "/grants/{grant_id}/reports/summary" in paths
        assert "/grants/{grant_id}/reports/excel" in paths
