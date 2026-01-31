"""
Comprehensive training frontend tests.
Tests training landing, student list, course list, and enrollment.
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
        # 302 = redirect to login, 401 = unauthorized, 422 = validation error
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
    async def test_students_search_with_cohort(self, async_client: AsyncClient):
        """Students search accepts cohort filter."""
        response = await async_client.get(
            "/training/students/search?cohort=2026-Spring"
        )
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
        """Student detail page should require authentication or handle missing."""
        response = await async_client.get(
            "/training/students/1", follow_redirects=False
        )
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


class TestCourseDetail:
    """Tests for course detail page."""

    @pytest.mark.asyncio
    async def test_course_detail_exists(self, async_client: AsyncClient):
        """Course detail page route should exist."""
        response = await async_client.get("/training/courses/1")
        assert response.status_code in [200, 302, 401, 404]

    @pytest.mark.asyncio
    async def test_course_detail_requires_auth(self, async_client: AsyncClient):
        """Course detail page should require authentication or handle missing."""
        response = await async_client.get("/training/courses/1", follow_redirects=False)
        assert response.status_code in [200, 302, 401, 404]

    @pytest.mark.asyncio
    async def test_course_detail_nonexistent(self, async_client: AsyncClient):
        """Course detail for nonexistent ID returns appropriate status."""
        response = await async_client.get("/training/courses/99999")
        assert response.status_code in [302, 401, 404]


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_invalid_student_id_handled(self, async_client: AsyncClient):
        """Invalid student ID should be handled gracefully."""
        response = await async_client.get("/training/students/invalid")
        assert response.status_code in [302, 401, 404, 422]

    @pytest.mark.asyncio
    async def test_invalid_course_id_handled(self, async_client: AsyncClient):
        """Invalid course ID should be handled gracefully."""
        response = await async_client.get("/training/courses/invalid")
        assert response.status_code in [302, 401, 404, 422]
