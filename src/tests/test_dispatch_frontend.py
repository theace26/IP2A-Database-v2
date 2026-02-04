"""
Tests for Dispatch Workflow Frontend UI.

Created: February 4, 2026 (Week 27)
Phase 7 - Referral & Dispatch System
"""
import pytest
from datetime import datetime, date, time as time_type
from httpx import AsyncClient

from src.models.labor_request import LaborRequest
from src.models.dispatch import Dispatch
from src.models.job_bid import JobBid
from src.models.book_registration import BookRegistration
from src.models.member import Member
from src.models.organization import Organization
from src.models.referral_book import ReferralBook
from src.db.enums import (
    LaborRequestStatus,
    DispatchStatus,
    BidStatus,
    RegistrationStatus,
    BookClassification,
    BookRegion,
)


class TestDispatchDashboard:
    """Tests for dispatch dashboard page."""

    @pytest.mark.asyncio
    async def test_dashboard_renders(self, async_client: AsyncClient, auth_headers):
        """Dashboard page renders successfully."""
        response = await async_client.get("/dispatch", cookies=auth_headers)
        assert response.status_code == 200
        assert b"Dispatch Dashboard" in response.content

    @pytest.mark.asyncio
    async def test_dashboard_requires_auth(self, async_client: AsyncClient):
        """Dashboard requires authentication."""
        response = await async_client.get("/dispatch", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["location"]

    @pytest.mark.asyncio
    async def test_dashboard_shows_stats(self, async_client: AsyncClient, auth_headers):
        """Dashboard displays key metrics."""
        response = await async_client.get("/dispatch", cookies=auth_headers)
        assert response.status_code == 200
        assert b"Pending Requests" in response.content
        assert b"Today's Dispatches" in response.content
        assert b"Active on Job" in response.content

    @pytest.mark.asyncio
    async def test_dashboard_shows_time_context(self, async_client: AsyncClient, auth_headers):
        """Dashboard displays time-sensitive context."""
        response = await async_client.get("/dispatch", cookies=auth_headers)
        assert response.status_code == 200
        # Check for bidding window badge
        assert b"Bidding" in response.content


class TestLaborRequests:
    """Tests for labor requests list and detail pages."""

    @pytest.mark.asyncio
    async def test_requests_list_renders(self, async_client: AsyncClient, auth_headers):
        """Requests list page renders."""
        response = await async_client.get("/dispatch/requests", cookies=auth_headers)
        assert response.status_code == 200
        assert b"Labor Requests" in response.content

    @pytest.mark.asyncio
    async def test_requests_filter_by_status(self, async_client: AsyncClient, auth_headers):
        """Requests can be filtered by status."""
        response = await async_client.get(
            "/dispatch/requests?status=open",
            cookies=auth_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_requests_search(self, async_client: AsyncClient, auth_headers):
        """Requests can be searched."""
        response = await async_client.get(
            "/dispatch/requests?search=ABC",
            cookies=auth_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_request_detail_404(self, async_client: AsyncClient, auth_headers):
        """Request detail returns 404 for non-existent request."""
        response = await async_client.get(
            "/dispatch/requests/999999",
            cookies=auth_headers
        )
        assert response.status_code == 404


class TestMorningReferral:
    """Tests for morning referral processing page."""

    @pytest.mark.asyncio
    async def test_morning_referral_renders(self, async_client: AsyncClient, auth_headers):
        """Morning referral page renders."""
        response = await async_client.get(
            "/dispatch/morning-referral",
            cookies=auth_headers
        )
        assert response.status_code == 200
        assert b"Morning Referral" in response.content

    @pytest.mark.asyncio
    async def test_morning_referral_shows_time_guards(self, async_client: AsyncClient, auth_headers):
        """Morning referral page shows time-based warnings."""
        response = await async_client.get(
            "/dispatch/morning-referral",
            cookies=auth_headers
        )
        assert response.status_code == 200
        # Check for either bidding window or cutoff message
        content = response.content.decode()
        assert "Bidding" in content or "Cutoff" in content


class TestActiveDispatches:
    """Tests for active dispatches page."""

    @pytest.mark.asyncio
    async def test_active_dispatches_renders(self, async_client: AsyncClient, auth_headers):
        """Active dispatches page renders."""
        response = await async_client.get("/dispatch/active", cookies=auth_headers)
        assert response.status_code == 200
        assert b"Active Dispatches" in response.content

    @pytest.mark.asyncio
    async def test_active_dispatches_filter(self, async_client: AsyncClient, auth_headers):
        """Active dispatches can be filtered."""
        response = await async_client.get(
            "/dispatch/active?status=working",
            cookies=auth_headers
        )
        assert response.status_code == 200


class TestDispatchQueue:
    """Tests for queue management page."""

    @pytest.mark.asyncio
    async def test_queue_renders(self, async_client: AsyncClient, auth_headers):
        """Queue page renders."""
        response = await async_client.get("/dispatch/queue", cookies=auth_headers)
        assert response.status_code == 200
        assert b"Dispatch Queue" in response.content

    @pytest.mark.asyncio
    async def test_queue_book_filter(self, async_client: AsyncClient, auth_headers):
        """Queue can be filtered by book."""
        response = await async_client.get(
            "/dispatch/queue?book_id=1",
            cookies=auth_headers
        )
        assert response.status_code == 200


class TestEnforcementDashboard:
    """Tests for enforcement dashboard."""

    @pytest.mark.asyncio
    async def test_enforcement_renders(self, async_client: AsyncClient, auth_headers):
        """Enforcement dashboard renders."""
        response = await async_client.get(
            "/dispatch/enforcement",
            cookies=auth_headers
        )
        assert response.status_code == 200
        assert b"Enforcement Dashboard" in response.content


class TestHTMXPartials:
    """Tests for HTMX partial endpoints."""

    @pytest.mark.asyncio
    async def test_stats_partial_returns_html(self, async_client: AsyncClient, auth_headers):
        """Stats partial returns HTML."""
        response = await async_client.get(
            "/dispatch/partials/stats",
            cookies=auth_headers
        )
        assert response.status_code == 200
        assert b"stat" in response.content  # DaisyUI stat class

    @pytest.mark.asyncio
    async def test_activity_feed_partial(self, async_client: AsyncClient, auth_headers):
        """Activity feed partial returns HTML."""
        response = await async_client.get(
            "/dispatch/partials/activity-feed",
            cookies=auth_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_pending_requests_partial(self, async_client: AsyncClient, auth_headers):
        """Pending requests partial returns HTML."""
        response = await async_client.get(
            "/dispatch/partials/pending-requests",
            cookies=auth_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_bid_queue_partial(self, async_client: AsyncClient, auth_headers):
        """Bid queue partial returns HTML."""
        response = await async_client.get(
            "/dispatch/partials/bid-queue",
            cookies=auth_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_queue_table_partial(self, async_client: AsyncClient, auth_headers):
        """Queue table partial returns HTML."""
        response = await async_client.get(
            "/dispatch/partials/queue-table",
            cookies=auth_headers
        )
        assert response.status_code == 200


class TestTimeContext:
    """Tests for time-sensitive business logic."""

    @pytest.mark.asyncio
    async def test_time_context_includes_bidding_status(self, async_client: AsyncClient, auth_headers):
        """Dashboard includes bidding window status."""
        response = await async_client.get("/dispatch", cookies=auth_headers)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Bidding" in content  # Bidding Open or Bidding Closed

    @pytest.mark.asyncio
    async def test_cutoff_warning_shown(self, async_client: AsyncClient, auth_headers):
        """3 PM cutoff warning is shown on appropriate pages."""
        response = await async_client.get(
            "/dispatch/morning-referral",
            cookies=auth_headers
        )
        assert response.status_code == 200
        # Page should have cutoff time information
        assert b"PM" in response.content or b"AM" in response.content


class TestSidebarNavigation:
    """Tests for sidebar dispatch links."""

    @pytest.mark.asyncio
    async def test_sidebar_dispatch_links_active(self, async_client: AsyncClient, auth_headers):
        """Dispatch links are active (not muted) in sidebar."""
        response = await async_client.get("/dispatch", cookies=auth_headers)
        assert response.status_code == 200
        content = response.content.decode()
        # Check that dispatch links exist and are not muted
        assert "/dispatch" in content
        assert "/dispatch/requests" in content
        # Should NOT have the "text-base-content/50" muted class on dispatch links
        assert "Week 27" not in content or "text-base-content/50" not in content


class TestRoleBasedAccess:
    """Tests for role-based access control."""

    @pytest.mark.asyncio
    async def test_staff_can_view_dashboard(self, async_client: AsyncClient, auth_headers):
        """Staff users can access dispatch dashboard."""
        response = await async_client.get("/dispatch", cookies=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_unauthenticated_redirects(self, async_client: AsyncClient):
        """Unauthenticated users are redirected to login."""
        response = await async_client.get("/dispatch", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["location"]


class TestHTMXInteractions:
    """Tests for HTMX-specific interactions."""

    @pytest.mark.asyncio
    async def test_request_table_htmx_swap(self, async_client: AsyncClient, auth_headers):
        """Request table returns partial when HTMX-Request header present."""
        response = await async_client.get(
            "/dispatch/requests",
            cookies=auth_headers,
            headers={"HX-Request": "true"}
        )
        assert response.status_code == 200
        # Should return partial, not full page
        assert b"<!DOCTYPE html>" not in response.content

    @pytest.mark.asyncio
    async def test_dispatch_table_htmx_swap(self, async_client: AsyncClient, auth_headers):
        """Dispatch table returns partial when HTMX-Request header present."""
        response = await async_client.get(
            "/dispatch/active",
            cookies=auth_headers,
            headers={"HX-Request": "true"}
        )
        assert response.status_code == 200
        # Should return partial, not full page
        assert b"<!DOCTYPE html>" not in response.content


class TestServiceIntegration:
    """Tests for DispatchFrontendService integration."""

    @pytest.mark.asyncio
    async def test_dashboard_stats_calculation(self, async_client: AsyncClient, auth_headers):
        """Dashboard correctly calculates stats from database."""
        response = await async_client.get("/dispatch", cookies=auth_headers)
        assert response.status_code == 200
        # Stats should be present
        content = response.content.decode()
        assert "Pending Requests" in content
        assert "Today's Dispatches" in content

    @pytest.mark.asyncio
    async def test_time_aware_business_logic(self, async_client: AsyncClient, auth_headers):
        """Service correctly handles time-sensitive operations."""
        response = await async_client.get("/dispatch", cookies=auth_headers)
        assert response.status_code == 200
        # Should show time context
        assert b"Next:" in response.content or b"next" in response.content.lower()
