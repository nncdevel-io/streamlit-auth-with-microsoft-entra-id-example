"""Tests for client module."""

import time
from typing import Any
from unittest.mock import MagicMock, patch

import jwt
import pytest
import requests
from cryptography.hazmat.primitives.asymmetric import rsa

from entra_id_auth_example.client import EntraAuthClient, IdTokenValidationError
from entra_id_auth_example.config import AuthConfig

_ISSUER = "https://login.microsoftonline.com/test-tenant-id/v2.0"
_NONCE = "test-nonce"
_SIGNING_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _make_id_token(key: rsa.RSAPrivateKey = _SIGNING_KEY, **overrides: Any) -> str:
    """Create a signed ID token with valid claims, overriding the given claims."""
    now = int(time.time())
    claims: dict[str, Any] = {
        "iss": _ISSUER,
        "aud": "test-client-id",
        "sub": "user-123",
        "name": "Test User",
        "nonce": _NONCE,
        "iat": now,
        "nbf": now,
        "exp": now + 3600,
    }
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "test-kid"})


def _create_client_with_keys() -> EntraAuthClient:
    """Create a client whose OIDC metadata resolves to the test signing key."""
    client = EntraAuthClient(
        AuthConfig(
            client_id="test-client-id",
            client_secret="test-secret",
            tenant_id="test-tenant-id",
            redirect_uri="http://localhost:8501/callback",
        )
    )
    jwks_client = MagicMock()
    jwks_client.get_signing_key_from_jwt.return_value = _SIGNING_KEY.public_key()
    client._issuer = _ISSUER
    client._jwks_client = jwks_client
    return client


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
        url = client.get_auth_url("test-state", "test-nonce")

        assert url == "https://login.example.com/auth"
        mock_app.get_authorization_request_url.assert_called_once_with(
            scopes=EntraAuthClient.SCOPES,
            state="test-state",
            redirect_uri="http://localhost:8501/callback",
            nonce="test-nonce",
        )

    @patch("entra_id_auth_example.client.ConfidentialClientApplication")
    def test_acquire_token_by_code_success(self, mock_msal: MagicMock) -> None:
        """Test successful token acquisition replaces claims with validated ones."""
        mock_app = MagicMock()
        mock_app.acquire_token_by_authorization_code.return_value = {
            "access_token": "test-access-token",
            "id_token": _make_id_token(),
            "id_token_claims": {"sub": "unvalidated"},
        }
        mock_msal.return_value = mock_app

        client = _create_client_with_keys()
        result = client.acquire_token_by_code("auth-code", nonce=_NONCE)

        assert result["access_token"] == "test-access-token"
        assert result["id_token_claims"]["sub"] == "user-123"

    @patch("entra_id_auth_example.client.ConfidentialClientApplication")
    def test_acquire_token_by_code_invalid_id_token(self, mock_msal: MagicMock) -> None:
        """Test that an ID token failing validation is turned into an error response."""
        mock_app = MagicMock()
        mock_app.acquire_token_by_authorization_code.return_value = {
            "access_token": "test-access-token",
            "id_token": _make_id_token(nonce="other-nonce"),
        }
        mock_msal.return_value = mock_app

        client = _create_client_with_keys()
        result = client.acquire_token_by_code("auth-code", nonce=_NONCE)

        assert result["error"] == "invalid_id_token"
        assert "access_token" not in result

    @patch("entra_id_auth_example.client.ConfidentialClientApplication")
    def test_acquire_token_by_code_missing_id_token(self, mock_msal: MagicMock) -> None:
        """Test that a response without an ID token is an error."""
        mock_app = MagicMock()
        mock_app.acquire_token_by_authorization_code.return_value = {
            "access_token": "test-access-token",
        }
        mock_msal.return_value = mock_app

        client = _create_client_with_keys()
        result = client.acquire_token_by_code("auth-code", nonce=_NONCE)

        assert result["error"] == "invalid_id_token"

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
        result = client.acquire_token_by_code("expired-code", nonce=_NONCE)

        assert "error" in result
        assert result["error"] == "invalid_grant"

    @patch("entra_id_auth_example.client.ConfidentialClientApplication")
    def test_logout_url(self, mock_msal: MagicMock) -> None:
        """Test logout_url property."""
        config = self._create_config()
        client = EntraAuthClient(config)

        assert "oauth2/v2.0/logout" in client.logout_url
        assert "post_logout_redirect_uri" in client.logout_url


@patch("entra_id_auth_example.client.ConfidentialClientApplication")
class TestValidateIdToken:
    """Tests for EntraAuthClient.validate_id_token."""

    def test_valid_token(self, mock_msal: MagicMock) -> None:
        """Test that a valid token returns its claims."""
        client = _create_client_with_keys()

        claims = client.validate_id_token(_make_id_token(), _NONCE)

        assert claims["sub"] == "user-123"

    @pytest.mark.parametrize(
        "overrides",
        [
            {"aud": "other-client-id"},
            {"iss": "https://login.microsoftonline.com/other-tenant/v2.0"},
            {"exp": int(time.time()) - 3600},
            {"nbf": int(time.time()) + 3600},
            {"nonce": "other-nonce"},
        ],
        ids=["aud", "iss", "exp", "nbf", "nonce"],
    )
    def test_invalid_claims(self, mock_msal: MagicMock, overrides: dict[str, Any]) -> None:
        """Test that a token with an invalid claim is rejected."""
        client = _create_client_with_keys()

        with pytest.raises(IdTokenValidationError):
            client.validate_id_token(_make_id_token(**overrides), _NONCE)

    def test_missing_nonce(self, mock_msal: MagicMock) -> None:
        """Test that a token without a nonce claim is rejected."""
        client = _create_client_with_keys()
        token = jwt.encode(
            {"iss": _ISSUER, "aud": "test-client-id", "sub": "u", "iat": 0, "exp": 2**31},
            _SIGNING_KEY,
            algorithm="RS256",
        )

        with pytest.raises(IdTokenValidationError):
            client.validate_id_token(token, _NONCE)

    def test_invalid_signature(self, mock_msal: MagicMock) -> None:
        """Test that a token signed with another key is rejected."""
        client = _create_client_with_keys()

        with pytest.raises(IdTokenValidationError):
            client.validate_id_token(_make_id_token(key=_OTHER_KEY), _NONCE)

    def test_unsigned_token(self, mock_msal: MagicMock) -> None:
        """Test that an unsigned (alg=none) token is rejected."""
        client = _create_client_with_keys()
        token = jwt.encode({"iss": _ISSUER, "nonce": _NONCE}, key=None, algorithm="none")

        with pytest.raises(IdTokenValidationError):
            client.validate_id_token(token, _NONCE)

    def test_metadata_fetch_failure(self, mock_msal: MagicMock) -> None:
        """Test that a failure to fetch OIDC metadata is reported as a validation error."""
        client = _create_client_with_keys()
        client._issuer = None
        client._http = MagicMock()
        client._http.get.side_effect = requests.ConnectionError("unreachable")

        with pytest.raises(IdTokenValidationError):
            client.validate_id_token(_make_id_token(), _NONCE)

    def test_metadata_is_fetched_once(self, mock_msal: MagicMock) -> None:
        """Test that OIDC metadata is fetched from the tenant's v2.0 endpoint and cached."""
        client = _create_client_with_keys()
        client._issuer = None
        client._jwks_client = None
        client._http = MagicMock()
        client._http.get.return_value.json.return_value = {
            "issuer": _ISSUER,
            "jwks_uri": "https://login.microsoftonline.com/test-tenant-id/discovery/v2.0/keys",
        }

        first = client._load_oidc_metadata()
        second = client._load_oidc_metadata()

        assert first == second
        assert first[0] == _ISSUER
        client._http.get.assert_called_once_with(
            "https://login.microsoftonline.com/test-tenant-id/v2.0/.well-known/openid-configuration",
            timeout=10,
        )
