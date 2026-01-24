# src/tests/conftest.py
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from src.main import app


@pytest_asyncio.fixture
async def async_client():
    """
    Async HTTP client for testing FastAPI endpoints.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
