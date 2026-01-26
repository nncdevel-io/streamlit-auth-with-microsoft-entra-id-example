"""Tests for client module."""

from unittest.mock import MagicMock, patch

from entra_id_auth_example.client import EntraAuthClient
from entra_id_auth_example.config import AuthConfig


class TestEntraAuthClient:
    """Tests for EntraAuthClient class."""

    @staticmethod
    def _create_config() -> AuthConfig:
        """Create a test configuration."""
        return AuthConfig(
            client_id="test-client-id",
            client_secret="test-secret",
            tenant_id="test-tenant-id",
            redirect_uri="http://localhost:8501/callback",
        )

    def test_scopes(self) -> None:
        """Test that SCOPES includes only non-reserved scopes.

        MSAL automatically adds reserved scopes (openid, profile, offline_access),
        so they must not be included explicitly.
        """
        reserved = {"openid", "profile", "offline_access"}
        assert not reserved.intersection(EntraAuthClient.SCOPES)
        assert "email" in EntraAuthClient.SCOPES

    @patch("entra_id_auth_example.client.ConfidentialClientApplication")
    def test_init_creates_msal_app(self, mock_msal: MagicMock) -> None:
        """Test that __init__ creates MSAL ConfidentialClientApplication."""
        config = self._create_config()
        EntraAuthClient(config)

        mock_msal.assert_called_once_with(
            client_id="test-client-id",
            client_credential="test-secret",
            authority="https://login.microsoftonline.com/test-tenant-id",
        )

    @patch("entra_id_auth_example.client.ConfidentialClientApplication")
    def test_get_auth_url(self, mock_msal: MagicMock) -> None:
        """Test get_auth_url returns authorization URL."""
        mock_app = MagicMock()
        mock_app.get_authorization_request_url.return_value = "https://login.example.com/auth"
        mock_msal.return_value = mock_app

        config = self._create_config()
        client = EntraAuthClient(config)
        url = client.get_auth_url("test-state")

        assert url == "https://login.example.com/auth"
        mock_app.get_authorization_request_url.assert_called_once_with(
            scopes=EntraAuthClient.SCOPES,
            state="test-state",
            redirect_uri="http://localhost:8501/callback",
        )

    @patch("entra_id_auth_example.client.ConfidentialClientApplication")
    def test_acquire_token_by_code_success(self, mock_msal: MagicMock) -> None:
        """Test successful token acquisition."""
        mock_app = MagicMock()
        mock_app.acquire_token_by_authorization_code.return_value = {
            "access_token": "test-access-token",
            "id_token_claims": {"sub": "user-123", "name": "Test User"},
        }
        mock_msal.return_value = mock_app

        config = self._create_config()
        client = EntraAuthClient(config)
        result = client.acquire_token_by_code("auth-code")

        assert result["access_token"] == "test-access-token"
        assert result["id_token_claims"]["sub"] == "user-123"

    @patch("entra_id_auth_example.client.ConfidentialClientApplication")
    def test_acquire_token_by_code_error(self, mock_msal: MagicMock) -> None:
        """Test token acquisition error handling."""
        mock_app = MagicMock()
        mock_app.acquire_token_by_authorization_code.return_value = {
            "error": "invalid_grant",
            "error_description": "The authorization code has expired.",
        }
        mock_msal.return_value = mock_app

        config = self._create_config()
        client = EntraAuthClient(config)
        result = client.acquire_token_by_code("expired-code")

        assert "error" in result
        assert result["error"] == "invalid_grant"

    @patch("entra_id_auth_example.client.ConfidentialClientApplication")
    def test_logout_url(self, mock_msal: MagicMock) -> None:
        """Test logout_url property."""
        config = self._create_config()
        client = EntraAuthClient(config)

        assert "oauth2/v2.0/logout" in client.logout_url
        assert "post_logout_redirect_uri" in client.logout_url
