"""
Comprehensive tests for report generation.
Tests report landing, PDF/Excel generation, and report service utilities.
"""

import pytest
from httpx import AsyncClient
from fastapi import status

from src.services.report_service import ReportService, _get_weasyprint

# Check if WeasyPrint is available for PDF tests
weasyprint_available = _get_weasyprint() is not False


class TestReportService:
    """Tests for ReportService utility methods."""

    def test_format_currency_positive(self):
        """Format positive currency correctly."""
        assert ReportService.format_currency(75.00) == "$75.00"
        assert ReportService.format_currency(1234.56) == "$1,234.56"
        assert ReportService.format_currency(0) == "$0.00"

    def test_format_currency_none(self):
        """Format None as zero."""
        assert ReportService.format_currency(None) == "$0.00"

    def test_format_currency_large(self):
        """Format large amounts with commas."""
        assert ReportService.format_currency(1000000.99) == "$1,000,000.99"

    def test_format_phone_standard(self):
        """Format 10-digit phone correctly."""
        assert ReportService.format_phone("2065551234") == "(206) 555-1234"
        assert ReportService.format_phone("1234567890") == "(123) 456-7890"

    def test_format_phone_none(self):
        """Format None phone as dash."""
        assert ReportService.format_phone(None) == "—"

    def test_format_phone_empty(self):
        """Format empty phone as dash."""
        assert ReportService.format_phone("") == "—"

    def test_format_phone_non_standard(self):
        """Return non-standard phone as-is."""
        assert ReportService.format_phone("123456") == "123456"
        assert ReportService.format_phone("+1 206-555-1234") == "+1 206-555-1234"

    def test_format_date_none(self):
        """Format None date as dash."""
        assert ReportService.format_date(None) == "—"

    def test_generate_excel_basic(self):
        """Generate Excel file from basic data."""
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25},
        ]
        columns = [
            {"key": "name", "header": "Name"},
            {"key": "age", "header": "Age"},
        ]

        result = ReportService.generate_excel(data, columns)

        assert isinstance(result, bytes)
        assert len(result) > 0
        # Excel files start with PK (zip format)
        assert result[:2] == b"PK"

    def test_generate_excel_with_title(self):
        """Generate Excel file with title row."""
        data = [{"name": "Test", "value": 100}]
        columns = [
            {"key": "name", "header": "Name"},
            {"key": "value", "header": "Value"},
        ]

        result = ReportService.generate_excel(
            data, columns, title="Test Report", sheet_name="Data"
        )

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_excel_empty_data(self):
        """Generate Excel file with no data rows."""
        data = []
        columns = [
            {"key": "name", "header": "Name"},
            {"key": "value", "header": "Value"},
        ]

        result = ReportService.generate_excel(data, columns)

        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.skipif(not weasyprint_available, reason="WeasyPrint not available")
    def test_generate_pdf_basic(self):
        """Generate PDF from basic HTML."""
        html = "<html><body><h1>Test Report</h1><p>Content here</p></body></html>"

        result = ReportService.generate_pdf(html)

        assert isinstance(result, bytes)
        assert len(result) > 0
        # PDF files start with %PDF
        assert result[:4] == b"%PDF"

    @pytest.mark.skipif(not weasyprint_available, reason="WeasyPrint not available")
    def test_generate_pdf_with_table(self):
        """Generate PDF with table content."""
        html = """
        <html>
        <body>
            <h1>Table Report</h1>
            <table>
                <tr><th>Name</th><th>Value</th></tr>
                <tr><td>Test</td><td>100</td></tr>
            </table>
        </body>
        </html>
        """

        result = ReportService.generate_pdf(html)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_pdf_raises_without_weasyprint(self):
        """PDF generation raises error when WeasyPrint unavailable."""
        if weasyprint_available:
            pytest.skip("WeasyPrint is available")

        with pytest.raises(RuntimeError, match="WeasyPrint is not available"):
            ReportService.generate_pdf("<html><body>Test</body></html>")


class TestReportsLanding:
    """Tests for reports landing page."""

    @pytest.mark.asyncio
    async def test_reports_landing_requires_auth(self, async_client: AsyncClient):
        """Reports landing should redirect to login when not authenticated."""
        response = await async_client.get("/reports", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_reports_landing_exists(self, async_client: AsyncClient):
        """Reports landing route should exist."""
        response = await async_client.get("/reports")
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestMemberReports:
    """Tests for member reports."""

    @pytest.mark.asyncio
    async def test_member_roster_pdf_requires_auth(self, async_client: AsyncClient):
        """Member roster PDF requires authentication."""
        response = await async_client.get(
            "/reports/members/roster?format=pdf", follow_redirects=False
        )
        assert response.status_code in [302, 401]

    @pytest.mark.asyncio
    async def test_member_roster_excel_requires_auth(self, async_client: AsyncClient):
        """Member roster Excel requires authentication."""
        response = await async_client.get(
            "/reports/members/roster?format=excel", follow_redirects=False
        )
        assert response.status_code in [302, 401]

    @pytest.mark.asyncio
    async def test_member_roster_route_exists(self, async_client: AsyncClient):
        """Member roster route should exist."""
        response = await async_client.get("/reports/members/roster?format=pdf")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_member_roster_with_status_filter(self, async_client: AsyncClient):
        """Member roster accepts status filter."""
        response = await async_client.get(
            "/reports/members/roster?format=excel&status=active"
        )
        assert response.status_code in [200, 302, 401]


class TestDuesReports:
    """Tests for dues reports."""

    @pytest.mark.asyncio
    async def test_dues_summary_pdf_requires_auth(self, async_client: AsyncClient):
        """Dues summary PDF requires authentication."""
        response = await async_client.get(
            "/reports/dues/summary?format=pdf", follow_redirects=False
        )
        assert response.status_code in [302, 401]

    @pytest.mark.asyncio
    async def test_dues_summary_excel_requires_auth(self, async_client: AsyncClient):
        """Dues summary Excel requires authentication."""
        response = await async_client.get(
            "/reports/dues/summary?format=excel", follow_redirects=False
        )
        assert response.status_code in [302, 401]

    @pytest.mark.asyncio
    async def test_dues_summary_route_exists(self, async_client: AsyncClient):
        """Dues summary route should exist."""
        response = await async_client.get("/reports/dues/summary?format=pdf")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_dues_summary_with_year(self, async_client: AsyncClient):
        """Dues summary accepts year parameter."""
        response = await async_client.get(
            "/reports/dues/summary?format=pdf&year=2025"
        )
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_overdue_report_pdf_requires_auth(self, async_client: AsyncClient):
        """Overdue report PDF requires authentication."""
        response = await async_client.get(
            "/reports/dues/overdue?format=pdf", follow_redirects=False
        )
        assert response.status_code in [302, 401]

    @pytest.mark.asyncio
    async def test_overdue_report_route_exists(self, async_client: AsyncClient):
        """Overdue report route should exist."""
        response = await async_client.get("/reports/dues/overdue?format=pdf")
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestTrainingReports:
    """Tests for training reports."""

    @pytest.mark.asyncio
    async def test_enrollment_report_requires_auth(self, async_client: AsyncClient):
        """Enrollment report requires authentication."""
        response = await async_client.get(
            "/reports/training/enrollment?format=excel", follow_redirects=False
        )
        assert response.status_code in [302, 401]

    @pytest.mark.asyncio
    async def test_enrollment_report_route_exists(self, async_client: AsyncClient):
        """Enrollment report route should exist."""
        response = await async_client.get("/reports/training/enrollment?format=excel")
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestOperationsReports:
    """Tests for operations reports."""

    @pytest.mark.asyncio
    async def test_grievance_report_requires_auth(self, async_client: AsyncClient):
        """Grievance report requires authentication."""
        response = await async_client.get(
            "/reports/operations/grievances?format=pdf", follow_redirects=False
        )
        assert response.status_code in [302, 401]

    @pytest.mark.asyncio
    async def test_grievance_report_route_exists(self, async_client: AsyncClient):
        """Grievance report route should exist."""
        response = await async_client.get("/reports/operations/grievances?format=pdf")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_salting_report_requires_auth(self, async_client: AsyncClient):
        """SALTing report requires authentication."""
        response = await async_client.get(
            "/reports/operations/salting?format=excel", follow_redirects=False
        )
        assert response.status_code in [302, 401]

    @pytest.mark.asyncio
    async def test_salting_report_route_exists(self, async_client: AsyncClient):
        """SALTing report route should exist."""
        response = await async_client.get("/reports/operations/salting?format=excel")
        assert response.status_code != status.HTTP_404_NOT_FOUND
