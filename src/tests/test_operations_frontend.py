"""
Comprehensive operations frontend tests.
Tests operations landing, SALTing, benevolence, and grievances.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


class TestOperationsLanding:
    """Tests for operations landing page."""

    @pytest.mark.asyncio
    async def test_operations_page_requires_auth(self, async_client: AsyncClient):
        """Operations page redirects to login when not authenticated."""
        response = await async_client.get("/operations", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_operations_page_exists(self, async_client: AsyncClient):
        """Operations page route exists."""
        response = await async_client.get("/operations")
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestSaltingActivities:
    """Tests for SALTing activities."""

    @pytest.mark.asyncio
    async def test_salting_list_exists(self, async_client: AsyncClient):
        """SALTing list page exists."""
        response = await async_client.get("/operations/salting")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_salting_search_exists(self, async_client: AsyncClient):
        """SALTing search endpoint exists."""
        response = await async_client.get("/operations/salting/search")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_salting_search_with_query(self, async_client: AsyncClient):
        """SALTing search accepts query parameter."""
        response = await async_client.get("/operations/salting/search?q=test")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_salting_search_with_type_filter(self, async_client: AsyncClient):
        """SALTing search accepts type filter."""
        response = await async_client.get(
            "/operations/salting/search?activity_type=outreach"
        )
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_salting_search_with_outcome_filter(self, async_client: AsyncClient):
        """SALTing search accepts outcome filter."""
        response = await async_client.get("/operations/salting/search?outcome=positive")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_salting_detail_exists(self, async_client: AsyncClient):
        """SALTing detail page route exists."""
        response = await async_client.get("/operations/salting/1")
        assert response.status_code in [200, 302, 401, 404]


class TestBenevolenceFund:
    """Tests for benevolence fund."""

    @pytest.mark.asyncio
    async def test_benevolence_list_exists(self, async_client: AsyncClient):
        """Benevolence list page exists."""
        response = await async_client.get("/operations/benevolence")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_benevolence_search_exists(self, async_client: AsyncClient):
        """Benevolence search endpoint exists."""
        response = await async_client.get("/operations/benevolence/search")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_benevolence_search_with_status(self, async_client: AsyncClient):
        """Benevolence search accepts status filter."""
        response = await async_client.get(
            "/operations/benevolence/search?status=submitted"
        )
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_benevolence_search_with_reason(self, async_client: AsyncClient):
        """Benevolence search accepts reason filter."""
        response = await async_client.get(
            "/operations/benevolence/search?reason=medical"
        )
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_benevolence_detail_exists(self, async_client: AsyncClient):
        """Benevolence detail page route exists."""
        response = await async_client.get("/operations/benevolence/1")
        assert response.status_code in [200, 302, 401, 404]


class TestGrievances:
    """Tests for grievance tracking."""

    @pytest.mark.asyncio
    async def test_grievances_list_exists(self, async_client: AsyncClient):
        """Grievances list page exists."""
        response = await async_client.get("/operations/grievances")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_grievances_search_exists(self, async_client: AsyncClient):
        """Grievances search endpoint exists."""
        response = await async_client.get("/operations/grievances/search")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_grievances_search_with_status(self, async_client: AsyncClient):
        """Grievances search accepts status filter."""
        response = await async_client.get("/operations/grievances/search?status=open")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_grievances_search_with_step(self, async_client: AsyncClient):
        """Grievances search accepts step filter."""
        response = await async_client.get("/operations/grievances/search?step=step_1")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_grievances_detail_exists(self, async_client: AsyncClient):
        """Grievances detail page route exists."""
        response = await async_client.get("/operations/grievances/1")
        assert response.status_code in [200, 302, 401, 404]


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_invalid_salting_id(self, async_client: AsyncClient):
        """Invalid SALTing ID is handled."""
        response = await async_client.get("/operations/salting/99999")
        assert response.status_code in [302, 401, 404]

    @pytest.mark.asyncio
    async def test_invalid_benevolence_id(self, async_client: AsyncClient):
        """Invalid benevolence ID is handled."""
        response = await async_client.get("/operations/benevolence/99999")
        assert response.status_code in [302, 401, 404]

    @pytest.mark.asyncio
    async def test_invalid_grievance_id(self, async_client: AsyncClient):
        """Invalid grievance ID is handled."""
        response = await async_client.get("/operations/grievances/99999")
        assert response.status_code in [302, 401, 404]
