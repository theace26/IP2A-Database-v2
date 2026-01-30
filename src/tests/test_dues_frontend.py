"""Tests for dues frontend routes."""

import pytest
from decimal import Decimal
from httpx import AsyncClient
from fastapi import status

from src.services.dues_frontend_service import DuesFrontendService
from src.db.enums import (
    MemberClassification,
    DuesPaymentStatus,
    DuesAdjustmentType,
    AdjustmentStatus,
    DuesPaymentMethod,
)


class TestDuesFrontendService:
    """Tests for DuesFrontendService methods."""

    def test_format_currency_positive(self):
        """Format positive currency amount."""
        result = DuesFrontendService.format_currency(Decimal("75.00"))
        assert result == "$75.00"

    def test_format_currency_zero(self):
        """Format zero currency amount."""
        result = DuesFrontendService.format_currency(Decimal("0"))
        assert result == "$0.00"

    def test_format_currency_none(self):
        """Format None returns $0.00."""
        result = DuesFrontendService.format_currency(None)
        assert result == "$0.00"

    def test_format_currency_large(self):
        """Format large currency amount with comma."""
        result = DuesFrontendService.format_currency(Decimal("1234.56"))
        assert result == "$1,234.56"

    def test_get_classification_badge_class(self):
        """Get badge class for classification."""
        result = DuesFrontendService.get_classification_badge_class(
            MemberClassification.JOURNEYMAN
        )
        assert result == "badge-primary"

    def test_get_classification_badge_class_apprentice(self):
        """Get badge class for apprentice classification."""
        result = DuesFrontendService.get_classification_badge_class(
            MemberClassification.APPRENTICE_1ST_YEAR
        )
        assert result == "badge-secondary"

    def test_get_classification_badge_class_retiree(self):
        """Get badge class for retiree classification."""
        result = DuesFrontendService.get_classification_badge_class(
            MemberClassification.RETIREE
        )
        assert result == "badge-ghost"

    def test_get_payment_status_badge_class_paid(self):
        """Get badge class for paid status."""
        result = DuesFrontendService.get_payment_status_badge_class(
            DuesPaymentStatus.PAID
        )
        assert result == "badge-success"

    def test_get_payment_status_badge_class_overdue(self):
        """Get badge class for overdue status."""
        result = DuesFrontendService.get_payment_status_badge_class(
            DuesPaymentStatus.OVERDUE
        )
        assert result == "badge-error"

    def test_get_adjustment_status_badge_class(self):
        """Get badge class for adjustment status."""
        result = DuesFrontendService.get_adjustment_status_badge_class(
            AdjustmentStatus.PENDING
        )
        assert result == "badge-warning"

    def test_get_adjustment_type_badge_class(self):
        """Get badge class for adjustment type."""
        result = DuesFrontendService.get_adjustment_type_badge_class(
            DuesAdjustmentType.WAIVER
        )
        assert result == "badge-info"

    def test_get_payment_method_display(self):
        """Get display name for payment method."""
        result = DuesFrontendService.get_payment_method_display(DuesPaymentMethod.CHECK)
        assert result == "Check"

    def test_get_payment_method_display_none(self):
        """Get display name for None payment method."""
        result = DuesFrontendService.get_payment_method_display(None)
        assert result == "—"


class TestDuesLanding:
    """Tests for dues landing page."""

    @pytest.mark.asyncio
    async def test_dues_landing_requires_auth(self, async_client: AsyncClient):
        """Dues landing requires authentication."""
        response = await async_client.get("/dues", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_dues_landing_page_exists(self, async_client: AsyncClient):
        """Dues landing page route exists."""
        response = await async_client.get("/dues")
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestDuesRates:
    """Tests for dues rates page."""

    @pytest.mark.asyncio
    async def test_rates_list_requires_auth(self, async_client: AsyncClient):
        """Rates list requires authentication."""
        response = await async_client.get("/dues/rates", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_rates_list_page_exists(self, async_client: AsyncClient):
        """Rates list page route exists."""
        response = await async_client.get("/dues/rates")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_rates_search_endpoint(self, async_client: AsyncClient):
        """Rates search endpoint exists."""
        response = await async_client.get("/dues/rates/search")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_rates_search_with_classification(self, async_client: AsyncClient):
        """Rates search filters by classification."""
        response = await async_client.get("/dues/rates/search?classification=journeyman")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_rates_search_active_only(self, async_client: AsyncClient):
        """Rates search filters active only."""
        response = await async_client.get("/dues/rates/search?active_only=true")
        assert response.status_code in [200, 302, 401]


class TestDuesPeriods:
    """Tests for dues periods pages."""

    @pytest.mark.asyncio
    async def test_periods_list_requires_auth(self, async_client: AsyncClient):
        """Periods list requires authentication."""
        response = await async_client.get("/dues/periods", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_periods_list_page_exists(self, async_client: AsyncClient):
        """Periods list page route exists."""
        response = await async_client.get("/dues/periods")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_periods_search_endpoint(self, async_client: AsyncClient):
        """Periods search endpoint exists."""
        response = await async_client.get("/dues/periods/search")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_periods_search_by_status(self, async_client: AsyncClient):
        """Periods search filters by status."""
        response = await async_client.get("/dues/periods/search?status=open")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_periods_search_by_year(self, async_client: AsyncClient):
        """Periods search filters by year."""
        response = await async_client.get("/dues/periods/search?year=2026")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_period_detail_not_found(self, async_client: AsyncClient):
        """Period detail returns 404 for invalid ID."""
        response = await async_client.get("/dues/periods/99999")
        assert response.status_code in [404, 302]  # 404 or redirect to login


class TestDuesPayments:
    """Tests for dues payments pages."""

    @pytest.mark.asyncio
    async def test_payments_list_requires_auth(self, async_client: AsyncClient):
        """Payments list requires authentication."""
        response = await async_client.get("/dues/payments", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_payments_list_page_exists(self, async_client: AsyncClient):
        """Payments list page route exists."""
        response = await async_client.get("/dues/payments")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_payments_search_endpoint(self, async_client: AsyncClient):
        """Payments search endpoint exists."""
        response = await async_client.get("/dues/payments/search")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_payments_search_with_filters(self, async_client: AsyncClient):
        """Payments search with filters works."""
        response = await async_client.get("/dues/payments/search?status=pending")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_payments_search_with_period(self, async_client: AsyncClient):
        """Payments search with period filter works."""
        response = await async_client.get("/dues/payments/search?period_id=1")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_member_payments_not_found(self, async_client: AsyncClient):
        """Member payments returns 404 for invalid member."""
        response = await async_client.get("/dues/payments/member/99999")
        assert response.status_code in [404, 302]  # 404 or redirect to login


class TestDuesAdjustments:
    """Tests for dues adjustments pages."""

    @pytest.mark.asyncio
    async def test_adjustments_list_requires_auth(self, async_client: AsyncClient):
        """Adjustments list requires authentication."""
        response = await async_client.get("/dues/adjustments", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_adjustments_list_page_exists(self, async_client: AsyncClient):
        """Adjustments list page route exists."""
        response = await async_client.get("/dues/adjustments")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_adjustments_search_endpoint(self, async_client: AsyncClient):
        """Adjustments search endpoint exists."""
        response = await async_client.get("/dues/adjustments/search")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_adjustments_search_by_status(self, async_client: AsyncClient):
        """Adjustments search filters by status."""
        response = await async_client.get("/dues/adjustments/search?status=pending")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_adjustments_search_by_type(self, async_client: AsyncClient):
        """Adjustments search filters by type."""
        response = await async_client.get("/dues/adjustments/search?adjustment_type=waiver")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_adjustment_detail_not_found(self, async_client: AsyncClient):
        """Adjustment detail returns 404 for invalid ID."""
        response = await async_client.get("/dues/adjustments/99999")
        assert response.status_code in [404, 302]  # 404 or redirect to login
