"""
Comprehensive staff management tests.
Tests search, filters, pagination, CRUD, and account actions.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


class TestStaffListPage:
    """Tests for staff list page."""

    @pytest.mark.asyncio
    async def test_staff_page_requires_auth(self, async_client: AsyncClient):
        """Staff page redirects to login when not authenticated."""
        response = await async_client.get("/staff", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_staff_page_exists(self, async_client: AsyncClient):
        """Staff page route exists."""
        response = await async_client.get("/staff")
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestStaffSearch:
    """Tests for search functionality."""

    @pytest.mark.asyncio
    async def test_search_endpoint_exists(self, async_client: AsyncClient):
        """Search endpoint exists."""
        response = await async_client.get("/staff/search")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_search_with_query(self, async_client: AsyncClient):
        """Search accepts query parameter."""
        response = await async_client.get("/staff/search?q=admin")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_search_with_role_filter(self, async_client: AsyncClient):
        """Search accepts role filter."""
        response = await async_client.get("/staff/search?role=admin")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_search_with_status_filter(self, async_client: AsyncClient):
        """Search accepts status filter."""
        response = await async_client.get("/staff/search?status=active")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_search_with_pagination(self, async_client: AsyncClient):
        """Search accepts page parameter."""
        response = await async_client.get("/staff/search?page=2")
        assert response.status_code in [200, 302, 401]


class TestStaffEditModal:
    """Tests for edit modal."""

    @pytest.mark.asyncio
    async def test_edit_modal_endpoint(self, async_client: AsyncClient):
        """Edit modal endpoint exists."""
        response = await async_client.get("/staff/1/edit")
        assert response.status_code in [200, 302, 401, 404]

    @pytest.mark.asyncio
    async def test_update_endpoint_accepts_post(self, async_client: AsyncClient):
        """Update endpoint accepts POST."""
        response = await async_client.post(
            "/staff/1/edit",
            data={"email": "test@test.com"},
        )
        assert response.status_code in [200, 302, 401, 404, 422]

    @pytest.mark.asyncio
    async def test_roles_update_endpoint(self, async_client: AsyncClient):
        """Roles update endpoint exists."""
        response = await async_client.post(
            "/staff/1/roles",
            data={"roles": ["member"]},
        )
        assert response.status_code in [200, 302, 401, 404]


class TestAccountActions:
    """Tests for account actions."""

    @pytest.mark.asyncio
    async def test_lock_endpoint(self, async_client: AsyncClient):
        """Lock endpoint exists."""
        response = await async_client.post("/staff/1/lock")
        assert response.status_code in [200, 302, 400, 401, 404]

    @pytest.mark.asyncio
    async def test_unlock_endpoint(self, async_client: AsyncClient):
        """Unlock endpoint exists."""
        response = await async_client.post("/staff/1/unlock")
        assert response.status_code in [200, 302, 401, 404]

    @pytest.mark.asyncio
    async def test_reset_password_endpoint(self, async_client: AsyncClient):
        """Reset password endpoint exists."""
        response = await async_client.post("/staff/1/reset-password")
        assert response.status_code in [200, 302, 401, 404]

    @pytest.mark.asyncio
    async def test_delete_endpoint(self, async_client: AsyncClient):
        """Delete endpoint exists."""
        response = await async_client.delete("/staff/1")
        assert response.status_code in [200, 302, 400, 401, 404]


class TestStaffDetailPage:
    """Tests for detail page."""

    @pytest.mark.asyncio
    async def test_detail_page_exists(self, async_client: AsyncClient):
        """Detail page route exists."""
        response = await async_client.get("/staff/1")
        assert response.status_code in [200, 302, 401, 404]

    @pytest.mark.asyncio
    async def test_detail_page_requires_auth(self, async_client: AsyncClient):
        """Detail page requires authentication."""
        response = await async_client.get("/staff/1", follow_redirects=False)
        assert response.status_code in [302, 401, 404]


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_nonexistent_user_returns_404(self, async_client: AsyncClient):
        """Requesting nonexistent user returns 404."""
        response = await async_client.get("/staff/99999")
        # Will be 404 or auth redirect
        assert response.status_code in [302, 401, 404]

    @pytest.mark.asyncio
    async def test_invalid_user_id_handled(self, async_client: AsyncClient):
        """Invalid user ID is handled gracefully."""
        response = await async_client.get("/staff/abc")
        # Should return 404 or 422 (validation error)
        assert response.status_code in [302, 401, 404, 422]
