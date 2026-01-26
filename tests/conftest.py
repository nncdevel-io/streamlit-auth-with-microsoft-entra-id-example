"""Pytest configuration and fixtures."""

import pytest

from entra_id_auth_example.config import AuthConfig


@pytest.fixture
def auth_config() -> AuthConfig:
    """Create a test AuthConfig instance."""
    return AuthConfig(
        client_id="test-client-id",
        client_secret="test-secret",
        tenant_id="test-tenant-id",
        redirect_uri="http://localhost:8501/callback",
    )
