"""Tests for authentication endpoints."""
import pytest
from unittest.mock import MagicMock, patch
from tests.conftest import create_mock_response


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_login_page_renders(self, client):
        """Test login page renders correctly."""
        response = client.get("/auth/login")
        assert response.status_code == 200
        assert "Login" in response.text or "login" in response.text.lower()

    def test_signup_page_renders(self, client):
        """Test signup page renders correctly."""
        response = client.get("/auth/signup")
        assert response.status_code == 200
        assert "Sign" in response.text or "signup" in response.text.lower()

    def test_csrf_endpoint(self, client):
        """Test CSRF token endpoint."""
        response = client.get("/auth/csrf")
        assert response.status_code == 200
        data = response.json()
        assert "csrf_token" in data
        assert len(data["csrf_token"]) > 0

    @patch('app.services.auth.AuthService.login')
    def test_login_form_success(self, mock_login, client, sample_user):
        """Test successful login form submission."""
        mock_login.return_value = {
            **sample_user,
            "access_token": "test-token",
            "refresh_token": "refresh-token",
            "expires_in": 3600
        }

        # Get CSRF token first
        csrf_response = client.get("/auth/csrf")
        csrf_token = csrf_response.json()["csrf_token"]

        response = client.post(
            "/auth/login/form",
            data={
                "email": "test@example.com",
                "password": "password123",
                "csrf_token": csrf_token
            },
            cookies={"csrf_token": csrf_token},
            follow_redirects=False
        )

        # Should redirect on success
        assert response.status_code == 303

    @patch('app.services.auth.AuthService.signup')
    def test_signup_form_success(self, mock_signup, client, sample_user):
        """Test successful signup form submission."""
        mock_signup.return_value = {
            **sample_user,
            "access_token": "test-token"
        }

        # Get CSRF token first
        csrf_response = client.get("/auth/csrf")
        csrf_token = csrf_response.json()["csrf_token"]

        response = client.post(
            "/auth/signup/form",
            data={
                "email": "new@example.com",
                "password": "password123",
                "username": "newuser",
                "csrf_token": csrf_token
            },
            cookies={"csrf_token": csrf_token},
            follow_redirects=False
        )

        # Should redirect on success
        assert response.status_code == 303

    def test_signup_form_invalid_csrf(self, client):
        """Test signup with invalid CSRF token."""
        response = client.post(
            "/auth/signup/form",
            data={
                "email": "new@example.com",
                "password": "password123",
                "username": "newuser",
                "csrf_token": "invalid-token"
            },
            cookies={"csrf_token": "different-token"}
        )

        # Should return error
        assert response.status_code in [400, 403]

    def test_login_form_invalid_csrf(self, client):
        """Test login with invalid CSRF token."""
        response = client.post(
            "/auth/login/form",
            data={
                "email": "test@example.com",
                "password": "password123",
                "csrf_token": "invalid-token"
            },
            cookies={"csrf_token": "different-token"}
        )

        # Should return error
        assert response.status_code in [400, 403]


class TestPasswordPolicy:
    """Test password policy enforcement."""

    def test_password_too_short(self, client):
        """Test password minimum length."""
        csrf_response = client.get("/auth/csrf")
        csrf_token = csrf_response.json()["csrf_token"]

        response = client.post(
            "/auth/signup/form",
            data={
                "email": "test@example.com",
                "password": "short1",  # Less than 8 chars
                "username": "testuser",
                "csrf_token": csrf_token
            },
            cookies={"csrf_token": csrf_token}
        )

        assert response.status_code == 400
        assert "8 characters" in response.text or "password" in response.text.lower()

    def test_password_no_letter(self, client):
        """Test password must contain letter."""
        csrf_response = client.get("/auth/csrf")
        csrf_token = csrf_response.json()["csrf_token"]

        response = client.post(
            "/auth/signup/form",
            data={
                "email": "test@example.com",
                "password": "12345678",  # No letters
                "username": "testuser",
                "csrf_token": csrf_token
            },
            cookies={"csrf_token": csrf_token}
        )

        assert response.status_code == 400

    def test_password_no_number(self, client):
        """Test password must contain number."""
        csrf_response = client.get("/auth/csrf")
        csrf_token = csrf_response.json()["csrf_token"]

        response = client.post(
            "/auth/signup/form",
            data={
                "email": "test@example.com",
                "password": "abcdefgh",  # No numbers
                "username": "testuser",
                "csrf_token": csrf_token
            },
            cookies={"csrf_token": csrf_token}
        )

        assert response.status_code == 400
