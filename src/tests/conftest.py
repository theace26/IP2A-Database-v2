# src/tests/conftest.py
"""
Test configuration and fixtures.

Note: Tests use the existing development database with transaction rollback
for isolation. Tables are managed via Alembic migrations, not create_all().
"""
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.db.session import get_db
from src.config.settings import settings


# Create engine once, reuse across tests
_engine = None


def get_test_engine():
    """Get or create the test database engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(str(settings.DATABASE_URL))
    return _engine


@pytest.fixture(scope="function")
def db_session():
    """
    Database session fixture for direct model testing.

    Uses the existing database (tables managed by Alembic migrations).
    Each test runs in a transaction that is rolled back after the test.

    Note: This session is NOT shared with the async_client. If you need
    to create data and access it via API, use the API to create the data
    or use the client_with_db fixture.
    """
    engine = get_test_engine()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create session with transaction isolation
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


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

    Note: This client uses a separate database session from db_session.
    Data created in db_session will NOT be visible to API calls.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def async_client_with_db():
    """
    Async HTTP client that shares a database transaction with db_session.

    Use this when tests need to:
    1. Create data directly in the database
    2. Access that data via API calls

    The transaction is rolled back after each test for isolation.
    """
    engine = get_test_engine()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create connection and transaction
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Override the get_db dependency to use our test session
    def override_get_db():
        try:
            yield session
        finally:
            pass  # Don't close - we manage the session lifecycle here

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client, session
    finally:
        # Clean up
        app.dependency_overrides.clear()
        session.close()
        transaction.rollback()
        connection.close()
