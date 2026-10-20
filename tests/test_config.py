"""Tests for config module."""

import os
from unittest.mock import patch

import pytest

from entra_id_auth_example.config import AuthConfig, load_config


class TestAuthConfig:
    """Tests for AuthConfig dataclass."""

    def test_authority_url(self) -> None:
        """Test authority property returns correct URL."""
        config = AuthConfig(
            client_id="test-client-id",
            client_secret="test-secret",
            tenant_id="test-tenant-id",
            redirect_uri="http://localhost:8501/callback",
            cookie_secret="test-cookie-secret",
        )
        assert config.authority == "https://login.microsoftonline.com/test-tenant-id"

    def test_server_metadata_url(self) -> None:
        """Test server_metadata_url points to the tenant's v2.0 OIDC metadata."""
        config = AuthConfig(
            client_id="test-client-id",
            client_secret="test-secret",
            tenant_id="test-tenant-id",
            redirect_uri="http://localhost:8501/callback",
            cookie_secret="test-cookie-secret",
        )
        assert config.server_metadata_url == (
            "https://login.microsoftonline.com/test-tenant-id/v2.0/.well-known/openid-configuration"
        )

    def test_to_streamlit_secrets(self) -> None:
        """Test to_streamlit_secrets returns the [auth] section for st.login()."""
        config = AuthConfig(
            client_id="test-client-id",
            client_secret="test-secret",
            tenant_id="test-tenant-id",
            redirect_uri="http://localhost:8501/callback",
            cookie_secret="test-cookie-secret",
        )
        assert config.to_streamlit_secrets() == {
            "auth": {
                "redirect_uri": "http://localhost:8501/callback",
                "cookie_secret": "test-cookie-secret",
                "client_id": "test-client-id",
                "client_secret": "test-secret",
                "server_metadata_url": config.server_metadata_url,
            }
        }

    def test_to_streamlit_secrets_with_ca_file(self) -> None:
        """Test SSL_CA_FILE is passed to httpx as verify via client_kwargs."""
        config = AuthConfig(
            client_id="test-client-id",
            client_secret="test-secret",
            tenant_id="test-tenant-id",
            redirect_uri="http://localhost:8501/callback",
            cookie_secret="test-cookie-secret",
            ssl_ca_file="/path/to/ca.pem",
        )
        assert config.to_streamlit_secrets()["auth"]["client_kwargs"] == {
            "verify": "/path/to/ca.pem"
        }

    def test_frozen_dataclass(self) -> None:
        """Test that AuthConfig is immutable."""
        config = AuthConfig(
            client_id="test-client-id",
            client_secret="test-secret",
            tenant_id="test-tenant-id",
            redirect_uri="http://localhost:8501/callback",
            cookie_secret="test-cookie-secret",
        )
        with pytest.raises(AttributeError):
            config.client_id = "new-id"  # type: ignore[misc]


class TestLoadConfigProduction:
    """Tests for load_config in production mode (ENV=production)."""

    def test_load_from_env_vars(self) -> None:
        """Test config loading from environment variables in production."""
        env_vars = {
            "ENV": "production",
            "AZURE_CLIENT_ID": "test-client-id",
            "AZURE_CLIENT_SECRET": "test-secret",
            "AZURE_TENANT_ID": "test-tenant-id",
            "AUTH_COOKIE_SECRET": "test-cookie-secret",
            "AZURE_REDIRECT_URI": "http://localhost:8501/callback",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            assert config.client_id == "test-client-id"
            assert config.client_secret == "test-secret"
            assert config.tenant_id == "test-tenant-id"
            assert config.redirect_uri == "http://localhost:8501/callback"

    def test_default_redirect_uri(self) -> None:
        """Test default redirect_uri when not specified."""
        env_vars = {
            "ENV": "production",
            "AZURE_CLIENT_ID": "test-client-id",
            "AZURE_CLIENT_SECRET": "test-secret",
            "AZURE_TENANT_ID": "test-tenant-id",
            "AUTH_COOKIE_SECRET": "test-cookie-secret",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            assert config.redirect_uri == "http://localhost:8501/callback"


class TestLoadConfigDevelopment:
    """Tests for load_config in development mode (reads from .env file)."""

    @patch("entra_id_auth_example.config.dotenv_values")
    def test_load_from_dotenv(self, mock_dotenv: patch) -> None:
        """Test config loading from .env file in development."""
        mock_dotenv.return_value = {
            "AZURE_CLIENT_ID": "dev-client-id",
            "AZURE_CLIENT_SECRET": "dev-secret",
            "AZURE_TENANT_ID": "dev-tenant-id",
            "AUTH_COOKIE_SECRET": "dev-cookie-secret",
            "AZURE_REDIRECT_URI": "http://localhost:8501/callback",
        }
        # Ensure ENV is not set to production
        with patch.dict(os.environ, {}, clear=True):
            config = load_config()
            assert config.client_id == "dev-client-id"
            mock_dotenv.assert_called_once_with(".env")

    @patch("entra_id_auth_example.config.dotenv_values")
    def test_missing_config_values(self, mock_dotenv: patch) -> None:
        """Test error when required values are missing."""
        mock_dotenv.return_value = {}
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                load_config()
            error_msg = str(exc_info.value)
            assert "AZURE_CLIENT_ID" in error_msg
            assert "AZURE_CLIENT_SECRET" in error_msg
            assert "AZURE_TENANT_ID" in error_msg
            assert "AUTH_COOKIE_SECRET" in error_msg

    @patch("entra_id_auth_example.config.dotenv_values")
    def test_ignores_env_vars_in_dev(self, mock_dotenv: patch) -> None:
        """Test that environment variables are ignored in development mode."""
        mock_dotenv.return_value = {
            "AZURE_CLIENT_ID": "from-dotenv",
            "AZURE_CLIENT_SECRET": "secret",
            "AZURE_TENANT_ID": "tenant",
            "AUTH_COOKIE_SECRET": "cookie-secret",
        }
        # Set env var that should be ignored
        with patch.dict(os.environ, {"AZURE_CLIENT_ID": "from-env"}, clear=True):
            config = load_config()
            # Should use value from .env, not environment
            assert config.client_id == "from-dotenv"
