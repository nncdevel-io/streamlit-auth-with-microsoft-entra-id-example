"""Tests for handlers module."""

from unittest.mock import MagicMock, patch

_CLAIMS = {
    "sub": "user-123",
    "name": "Test User",
    "email": "test@example.com",
    "iss": "https://login.microsoftonline.com/tenant/v2.0",
}


def _mock_user(mock_st: MagicMock, claims: dict[str, str] | None) -> None:
    """Configure st.user as logged in with the given claims, or logged out when None."""
    mock_st.user.is_logged_in = claims is not None
    mock_st.user.to_dict.return_value = {"is_logged_in": claims is not None, **(claims or {})}


class TestIsAuthenticated:
    """Tests for is_authenticated function."""

    @patch("entra_id_auth_example.handlers.st")
    def test_authenticated_true(self, mock_st: MagicMock) -> None:
        """Test returns True when user is logged in."""
        _mock_user(mock_st, _CLAIMS)

        from entra_id_auth_example.handlers import is_authenticated

        assert is_authenticated() is True

    @patch("entra_id_auth_example.handlers.st")
    def test_authenticated_false(self, mock_st: MagicMock) -> None:
        """Test returns False when user is not logged in."""
        _mock_user(mock_st, None)

        from entra_id_auth_example.handlers import is_authenticated

        assert is_authenticated() is False


class TestGetCurrentUser:
    """Tests for get_current_user function."""

    @patch("entra_id_auth_example.handlers.st")
    def test_get_user_authenticated(self, mock_st: MagicMock) -> None:
        """Test returns user info extracted from claims when logged in."""
        _mock_user(mock_st, _CLAIMS)

        from entra_id_auth_example.handlers import get_current_user

        assert get_current_user() == {
            "id": "user-123",
            "name": "Test User",
            "email": "test@example.com",
        }

    @patch("entra_id_auth_example.handlers.st")
    def test_email_falls_back_to_preferred_username(self, mock_st: MagicMock) -> None:
        """Test uses preferred_username when the email claim is missing."""
        _mock_user(mock_st, {"sub": "user-123", "name": "Test User", "preferred_username": "u@x"})

        from entra_id_auth_example.handlers import get_current_user

        user = get_current_user()
        assert user is not None
        assert user["email"] == "u@x"

    @patch("entra_id_auth_example.handlers.st")
    def test_get_user_not_authenticated(self, mock_st: MagicMock) -> None:
        """Test returns None when not logged in."""
        _mock_user(mock_st, None)

        from entra_id_auth_example.handlers import get_current_user

        assert get_current_user() is None


class TestGetTokenClaims:
    """Tests for get_token_claims function."""

    @patch("entra_id_auth_example.handlers.st")
    def test_get_claims_authenticated(self, mock_st: MagicMock) -> None:
        """Test returns claims from st.user when logged in."""
        _mock_user(mock_st, _CLAIMS)

        from entra_id_auth_example.handlers import get_token_claims

        claims = get_token_claims()
        assert claims is not None
        assert claims["sub"] == "user-123"
        assert claims["iss"] == _CLAIMS["iss"]

    @patch("entra_id_auth_example.handlers.st")
    def test_get_claims_not_authenticated(self, mock_st: MagicMock) -> None:
        """Test returns None when not logged in."""
        _mock_user(mock_st, None)

        from entra_id_auth_example.handlers import get_token_claims

        assert get_token_claims() is None


class TestLoginLogout:
    """Tests for login and logout functions."""

    @patch("entra_id_auth_example.handlers.st")
    def test_login_delegates_to_st_login(self, mock_st: MagicMock) -> None:
        """Test login() calls st.login()."""
        from entra_id_auth_example.handlers import login

        login()
        mock_st.login.assert_called_once_with()

    @patch("entra_id_auth_example.handlers.st")
    def test_logout_delegates_to_st_logout(self, mock_st: MagicMock) -> None:
        """Test logout() calls st.logout()."""
        from entra_id_auth_example.handlers import logout

        logout()
        mock_st.logout.assert_called_once_with()


class TestRequireAuth:
    """Tests for require_auth function."""

    @patch("entra_id_auth_example.handlers.st")
    def test_authenticated_passes(self, mock_st: MagicMock) -> None:
        """Test does not stop when logged in."""
        _mock_user(mock_st, _CLAIMS)

        from entra_id_auth_example.handlers import require_auth

        require_auth()
        mock_st.stop.assert_not_called()

    @patch("entra_id_auth_example.handlers.st")
    def test_not_authenticated_stops(self, mock_st: MagicMock) -> None:
        """Test calls st.stop() when not logged in."""
        _mock_user(mock_st, None)
        mock_st.button.return_value = False

        from entra_id_auth_example.handlers import require_auth

        require_auth()
        mock_st.error.assert_called_once()
        mock_st.stop.assert_called_once()
