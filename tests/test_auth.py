"""
Authentication tests for Zinzino IoT API.

Tests for user registration, login, token management, and OAuth.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.auth
class TestUserRegistration:
    """Test user registration functionality."""
    
    def test_register_user(self, client: TestClient, mock_user_data: dict):
        """Test successful user registration."""
        response = client.post("/api/v1/auth/register", json=mock_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == mock_user_data["email"]
        assert data["user"]["full_name"] == mock_user_data["full_name"]
    
    def test_register_duplicate_email(self, client: TestClient, registered_user: dict):
        """Test registration with duplicate email fails."""
        # Try to register with same email
        response = client.post(
            "/api/v1/auth/register",
            json=registered_user["user_data"]
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email format."""
        data = {
            "email": "invalid-email",
            "password": "Test1234!",
            "full_name": "Test User",
            "language": "en",
            "timezone": "Europe/Istanbul"
        }
        response = client.post("/api/v1/auth/register", json=data)
        
        assert response.status_code == 422
    
    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password."""
        data = {
            "email": "test@example.com",
            "password": "weak",
            "full_name": "Test User",
            "language": "en",
            "timezone": "Europe/Istanbul"
        }
        response = client.post("/api/v1/auth/register", json=data)
        
        assert response.status_code == 422


@pytest.mark.auth
class TestUserLogin:
    """Test user login functionality."""
    
    def test_login_success(self, client: TestClient, registered_user: dict):
        """Test successful login with correct credentials."""
        credentials = {
            "email": registered_user["user_data"]["email"],
            "password": registered_user["user_data"]["password"]
        }
        response = client.post("/api/v1/auth/login", json=credentials)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client: TestClient, registered_user: dict):
        """Test login fails with invalid password."""
        credentials = {
            "email": registered_user["user_data"]["email"],
            "password": "WrongPassword123!"
        }
        response = client.post("/api/v1/auth/login", json=credentials)
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login fails with non-existent email."""
        credentials = {
            "email": "nonexistent@example.com",
            "password": "Test1234!"
        }
        response = client.post("/api/v1/auth/login", json=credentials)
        
        assert response.status_code == 401


@pytest.mark.auth
class TestTokenManagement:
    """Test JWT token management."""
    
    def test_refresh_token(self, client: TestClient, registered_user: dict):
        """Test token refresh with valid refresh token."""
        refresh_token = registered_user["response"]["refresh_token"]
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_refresh_invalid_token(self, client: TestClient):
        """Test refresh fails with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"}
        )
        
        assert response.status_code in [401, 500]
    
    def test_access_protected_endpoint(self, client: TestClient, auth_headers: dict):
        """Test accessing protected endpoint with valid token."""
        response = client.get("/api/v1/devices", headers=auth_headers)
        
        assert response.status_code == 200
    
    def test_access_protected_endpoint_no_token(self, client: TestClient):
        """Test accessing protected endpoint without token fails."""
        response = client.get("/api/v1/devices")
        
        assert response.status_code == 401


@pytest.mark.auth
class TestLogout:
    """Test logout functionality."""
    
    def test_logout(self, client: TestClient, auth_headers: dict):
        """Test user logout."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_logout_without_auth(self, client: TestClient):
        """Test logout without authentication fails."""
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code == 401


@pytest.mark.auth
class TestPasswordReset:
    """Test password reset functionality."""
    
    def test_forgot_password(self, client: TestClient, registered_user: dict):
        """Test password reset request."""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": registered_user["user_data"]["email"]}
        )
        
        # Should always return success for security
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_forgot_password_nonexistent_email(self, client: TestClient):
        """Test password reset with non-existent email."""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"}
        )
        
        # Should return success even for non-existent email (security)
        assert response.status_code == 200
