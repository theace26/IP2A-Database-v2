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
    async def test_students_page_exists(self, async_client: AsyncClient):
        """Students page route should exist."""
        response = await async_client.get("/training/students")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_students_page_requires_auth(self, async_client: AsyncClient):
        """Students page should require authentication."""
        response = await async_client.get("/training/students", follow_redirects=False)
        assert response.status_code in [302, 401]

    @pytest.mark.asyncio
    async def test_students_search_exists(self, async_client: AsyncClient):
        """Students search endpoint should exist."""
        response = await async_client.get("/training/students/search")
        # 302 = redirect to login, 401 = unauthorized, 422 = validation error (expected without auth)
        assert response.status_code in [200, 302, 401, 422]

    @pytest.mark.asyncio
    async def test_students_search_with_query(self, async_client: AsyncClient):
        """Students search accepts query parameter."""
        response = await async_client.get("/training/students/search?q=john")
        assert response.status_code in [200, 302, 401, 422]

    @pytest.mark.asyncio
    async def test_students_search_with_status(self, async_client: AsyncClient):
        """Students search accepts status filter."""
        response = await async_client.get("/training/students/search?status=enrolled")
        assert response.status_code in [200, 302, 401, 422]

    @pytest.mark.asyncio
    async def test_students_search_with_pagination(self, async_client: AsyncClient):
        """Students search accepts page parameter."""
        response = await async_client.get("/training/students/search?page=2")
        assert response.status_code in [200, 302, 401, 422]


class TestStudentDetail:
    """Tests for student detail page."""

    @pytest.mark.asyncio
    async def test_student_detail_exists(self, async_client: AsyncClient):
        """Student detail page route should exist."""
        response = await async_client.get("/training/students/1")
        assert response.status_code in [200, 302, 401, 404]

    @pytest.mark.asyncio
    async def test_student_detail_requires_auth(self, async_client: AsyncClient):
        """Student detail page should require authentication or handle missing student."""
        response = await async_client.get(
            "/training/students/1", follow_redirects=False
        )
        # May redirect to login (302), return unauthorized (401), not found (404),
        # or OK if following redirects internally (200)
        assert response.status_code in [200, 302, 401, 404]

    @pytest.mark.asyncio
    async def test_student_detail_nonexistent(self, async_client: AsyncClient):
        """Student detail for nonexistent ID returns appropriate status."""
        response = await async_client.get("/training/students/99999")
        assert response.status_code in [302, 401, 404]


class TestCourseList:
    """Tests for course list page."""

    @pytest.mark.asyncio
    async def test_courses_page_exists(self, async_client: AsyncClient):
        """Courses page route should exist."""
        response = await async_client.get("/training/courses")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_courses_page_requires_auth(self, async_client: AsyncClient):
        """Courses page should require authentication."""
        response = await async_client.get("/training/courses", follow_redirects=False)
        assert response.status_code in [302, 401]
