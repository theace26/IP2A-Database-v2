"""Tests for dues frontend routes."""

import pytest
from decimal import Decimal
from httpx import AsyncClient
from fastapi import status

from src.services.dues_frontend_service import DuesFrontendService
from src.db.enums import MemberClassification, DuesPaymentStatus, AdjustmentStatus, DuesAdjustmentType


class TestDuesFrontendService:
    """Tests for DuesFrontendService."""

    def test_format_currency_positive(self):
        """Format positive currency amount."""
        result = DuesFrontendService.format_currency(Decimal("75.00"))
        assert result == "$75.00"

    def test_format_currency_large(self):
        """Format large currency amount with comma."""
        result = DuesFrontendService.format_currency(Decimal("1234.56"))
        assert result == "$1,234.56"

    def test_format_currency_none(self):
        """Format None returns $0.00."""
        result = DuesFrontendService.format_currency(None)
        assert result == "$0.00"

    def test_format_currency_zero(self):
        """Format zero returns $0.00."""
        result = DuesFrontendService.format_currency(Decimal("0"))
        assert result == "$0.00"

    def test_get_classification_badge_class_journeyman(self):
        """Get badge class for journeyman classification."""
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
        """Get badge class for paid payment status."""
        result = DuesFrontendService.get_payment_status_badge_class(
            DuesPaymentStatus.PAID
        )
        assert result == "badge-success"

    def test_get_payment_status_badge_class_overdue(self):
        """Get badge class for overdue payment status."""
        result = DuesFrontendService.get_payment_status_badge_class(
            DuesPaymentStatus.OVERDUE
        )
        assert result == "badge-error"

    def test_get_adjustment_status_badge_class_pending(self):
        """Get badge class for pending adjustment status."""
        result = DuesFrontendService.get_adjustment_status_badge_class(
            AdjustmentStatus.PENDING
        )
        assert result == "badge-warning"

    def test_get_adjustment_type_badge_class_waiver(self):
        """Get badge class for waiver adjustment type."""
        result = DuesFrontendService.get_adjustment_type_badge_class(
            DuesAdjustmentType.WAIVER
        )
        assert result == "badge-info"


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
    async def test_rates_search_endpoint_exists(self, async_client: AsyncClient):
        """Rates search endpoint exists."""
        response = await async_client.get("/dues/rates/search")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_rates_search_with_classification(self, async_client: AsyncClient):
        """Rates search accepts classification filter."""
        response = await async_client.get("/dues/rates/search?classification=journeyman")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_rates_search_with_active_only(self, async_client: AsyncClient):
        """Rates search accepts active_only filter."""
        response = await async_client.get("/dues/rates/search?active_only=true")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_rates_search_with_both_filters(self, async_client: AsyncClient):
        """Rates search accepts both filters together."""
        response = await async_client.get(
            "/dues/rates/search?classification=journeyman&active_only=true"
        )
        assert response.status_code in [200, 302, 401]
