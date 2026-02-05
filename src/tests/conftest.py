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
from datetime import datetime

from src.main import app
from src.db.session import get_db
from src.config.settings import settings
from src.models.user import User
from src.models.role import Role
from src.models.user_role import UserRole
from src.models.member import Member
from src.core.jwt import create_access_token
from src.core.security import hash_password


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


@pytest.fixture(scope="function")
def test_user(db_session):
    """
    Create a test user with admin role for authentication tests.
    """
    # Check if admin role exists
    admin_role = db_session.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        admin_role = Role(
            name="admin",
            display_name="Administrator",
            description="Administrator"
        )
        db_session.add(admin_role)
        db_session.flush()

    # Check if test user already exists (from previous failed test run)
    existing_user = db_session.query(User).filter(User.email == "test@example.com").first()
    if existing_user:
        # Delete existing user to start fresh
        db_session.query(UserRole).filter(UserRole.user_id == existing_user.id).delete()
        db_session.delete(existing_user)
        db_session.flush()

    # Create test user
    user = User(
        email="test@example.com",
        password_hash=hash_password("testpassword"),
        first_name="Test",
        last_name="User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    # Assign admin role
    user_role = UserRole(user_id=user.id, role_id=admin_role.id)
    db_session.add(user_role)
    db_session.flush()

    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """
    Create authentication headers with Bearer token for the test user.
    """
    token = create_access_token(
        subject=test_user.id,
        additional_claims={
            "email": test_user.email,
            "roles": ["admin"],
        },
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def test_member(db_session):
    """
    Create a test member for member-related tests.
    """
    # Check if test member already exists (from previous failed test run)
    existing_member = db_session.query(Member).filter(Member.member_number == "TEST001").first()
    if existing_member:
        # Delete existing member to start fresh
        db_session.delete(existing_member)
        db_session.flush()

    member = Member(
        member_number="TEST001",
        first_name="Test",
        last_name="Member",
        classification="journeyman_wireman",
        status="active",
    )
    db_session.add(member)
    db_session.flush()
    return member
