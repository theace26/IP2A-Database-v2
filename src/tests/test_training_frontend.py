"""
Training frontend tests.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


class TestTrainingLanding:
    """Tests for training landing page."""

    @pytest.mark.asyncio
    async def test_training_page_requires_auth(self, async_client: AsyncClient):
        """Training page should redirect to login when not authenticated."""
        response = await async_client.get("/training", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_training_page_exists(self, async_client: AsyncClient):
        """Training page route should exist."""
        response = await async_client.get("/training")
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestStudentList:
    """Tests for student list page."""

    @pytest.mark.asyncio
    async def test_students_page_requires_auth(self, async_client: AsyncClient):
        """Students page should redirect to login when not authenticated."""
        response = await async_client.get("/training/students", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_students_page_exists(self, async_client: AsyncClient):
        """Students page route should exist."""
        response = await async_client.get("/training/students")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_students_search_exists(self, async_client: AsyncClient):
        """Students search endpoint should exist."""
        response = await async_client.get("/training/students/search")
        # 302 = redirect to login, 401 = unauthorized, 422 = validation error (expected without auth)
        assert response.status_code in [200, 302, 401, 422]


class TestCourseList:
    """Tests for course list page."""

    @pytest.mark.asyncio
    async def test_courses_page_requires_auth(self, async_client: AsyncClient):
        """Courses page should redirect to login when not authenticated."""
        response = await async_client.get("/training/courses", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_courses_page_exists(self, async_client: AsyncClient):
        """Courses page route should exist."""
        response = await async_client.get("/training/courses")
        assert response.status_code != status.HTTP_404_NOT_FOUND
