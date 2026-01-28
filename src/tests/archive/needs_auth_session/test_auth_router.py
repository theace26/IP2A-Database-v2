"""Tests for authentication router endpoints."""

import uuid
from fastapi.testclient import TestClient

from src.models.user import User
from src.core.security import hash_password


class TestLoginEndpoint:
    """Tests for /auth/login endpoint."""

    def test_login_success(self, client: TestClient, db_session):
        """Test successful login."""
        email = f"login_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash=hash_password("password123"),
            first_name="Login",
            last_name="Test",
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "password123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, db_session):
        """Test login with wrong password."""
        email = f"wrongpw_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash=hash_password("correctpassword"),
            first_name="Wrong",
            last_name="PW",
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with nonexistent email."""
        response = client.post(
            "/auth/login",
            json={
                "email": "nobody@example.com",
                "password": "password",
            },
        )

        assert response.status_code == 401


class TestMeEndpoint:
    """Tests for /auth/me endpoint."""

    def test_me_authenticated(self, client: TestClient, db_session):
        """Test getting current user info."""
        email = f"me_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash=hash_password("password123"),
            first_name="Current",
            last_name="User",
        )
        db_session.add(user)
        db_session.commit()

        # Login first
        login_response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "password123",
            },
        )
        access_token = login_response.json()["access_token"]

        # Get /me
        response = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email
        assert data["first_name"] == "Current"
        assert data["last_name"] == "User"

    def test_me_unauthenticated(self, client: TestClient):
        """Test /me without token."""
        response = client.get("/auth/me")
        assert response.status_code == 401


class TestRefreshEndpoint:
    """Tests for /auth/refresh endpoint."""

    def test_refresh_success(self, client: TestClient, db_session):
        """Test token refresh."""
        email = f"refresh_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash=hash_password("password123"),
            first_name="Refresh",
            last_name="Test",
        )
        db_session.add(user)
        db_session.commit()

        # Login
        login_response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "password123",
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh
        response = client.post(
            "/auth/refresh",
            json={
                "refresh_token": refresh_token,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


class TestLogoutEndpoint:
    """Tests for /auth/logout endpoint."""

    def test_logout_success(self, client: TestClient, db_session):
        """Test logout."""
        email = f"logout_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash=hash_password("password123"),
            first_name="Logout",
            last_name="Test",
        )
        db_session.add(user)
        db_session.commit()

        # Login
        login_response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "password123",
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        # Logout
        response = client.post(
            "/auth/logout",
            json={
                "refresh_token": refresh_token,
            },
        )

        assert response.status_code == 204

        # Refresh should fail now
        refresh_response = client.post(
            "/auth/refresh",
            json={
                "refresh_token": refresh_token,
            },
        )
        assert refresh_response.status_code == 401
