"""
Staff management tests.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


class TestStaffList:
    """Tests for staff list page."""

    @pytest.mark.asyncio
    async def test_staff_page_requires_auth(self, async_client: AsyncClient):
        """Staff page should redirect to login when not authenticated."""
        response = await async_client.get("/staff", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_staff_page_exists(self, async_client: AsyncClient):
        """Staff page endpoint should exist (not 404)."""
        response = await async_client.get("/staff")
        # Will redirect to login without auth, but endpoint exists
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestStaffSearch:
    """Tests for staff search functionality."""

    @pytest.mark.asyncio
    async def test_search_endpoint_requires_auth(self, async_client: AsyncClient):
        """Staff search should require authentication."""
        response = await async_client.get("/staff/search", follow_redirects=False)
        # Returns 302 (redirect to login) or 401 when not authenticated
        assert response.status_code in [status.HTTP_302_FOUND, status.HTTP_401_UNAUTHORIZED]

    @pytest.mark.asyncio
    async def test_search_endpoint_exists(self, async_client: AsyncClient):
        """Staff search endpoint should exist (not 404)."""
        response = await async_client.get("/staff/search?q=test")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_search_with_filters(self, async_client: AsyncClient):
        """Staff search with filters should not return 404."""
        response = await async_client.get(
            "/staff/search?q=admin&role=admin&status=active&page=1"
        )
        assert response.status_code != status.HTTP_404_NOT_FOUND
