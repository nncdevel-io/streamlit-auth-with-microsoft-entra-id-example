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
        )
        assert config.authority == "https://login.microsoftonline.com/test-tenant-id"

    def test_base_url(self) -> None:
        """Test base_url property extracts base URL from redirect_uri."""
        config = AuthConfig(
            client_id="test-client-id",
            client_secret="test-secret",
            tenant_id="test-tenant-id",
            redirect_uri="http://localhost:8501/callback",
        )
        assert config.base_url == "http://localhost:8501/"

    def test_logout_url(self) -> None:
        """Test logout_url property includes post_logout_redirect_uri."""
        config = AuthConfig(
            client_id="test-client-id",
            client_secret="test-secret",
            tenant_id="test-tenant-id",
            redirect_uri="http://localhost:8501/callback",
        )
        assert "oauth2/v2.0/logout" in config.logout_url
        assert "post_logout_redirect_uri" in config.logout_url

    def test_frozen_dataclass(self) -> None:
        """Test that AuthConfig is immutable."""
        config = AuthConfig(
            client_id="test-client-id",
            client_secret="test-secret",
            tenant_id="test-tenant-id",
            redirect_uri="http://localhost:8501/callback",
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
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            assert config.redirect_uri == "http://localhost:8501/"


class TestLoadConfigDevelopment:
    """Tests for load_config in development mode (reads from .env file)."""

    @patch("entra_id_auth_example.config.dotenv_values")
    def test_load_from_dotenv(self, mock_dotenv: patch) -> None:
        """Test config loading from .env file in development."""
        mock_dotenv.return_value = {
            "AZURE_CLIENT_ID": "dev-client-id",
            "AZURE_CLIENT_SECRET": "dev-secret",
            "AZURE_TENANT_ID": "dev-tenant-id",
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

    @patch("entra_id_auth_example.config.dotenv_values")
    def test_ignores_env_vars_in_dev(self, mock_dotenv: patch) -> None:
        """Test that environment variables are ignored in development mode."""
        mock_dotenv.return_value = {
            "AZURE_CLIENT_ID": "from-dotenv",
            "AZURE_CLIENT_SECRET": "secret",
            "AZURE_TENANT_ID": "tenant",
        }
        # Set env var that should be ignored
        with patch.dict(os.environ, {"AZURE_CLIENT_ID": "from-env"}, clear=True):
            config = load_config()
            # Should use value from .env, not environment
            assert config.client_id == "from-dotenv"
