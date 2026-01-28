# src/tests/conftest.py
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.db.base import Base
from src.config.settings import settings


@pytest.fixture(scope="function")
def db_session():
    """
    Database session fixture for direct model testing.
    Creates a new session for each test and rolls back after.
    """
    # Use test database
    engine = create_engine(str(settings.DATABASE_URL))
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client():
    """
    Synchronous HTTP client for testing FastAPI endpoints.
    """
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client():
    """
    Async HTTP client for testing FastAPI endpoints.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
