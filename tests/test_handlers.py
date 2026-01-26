"""Tests for handlers module."""

from unittest.mock import MagicMock, patch


class TestIsAuthenticated:
    """Tests for is_authenticated function."""

    @patch("entra_id_auth_example.handlers.st")
    def test_authenticated_true(self, mock_st: MagicMock) -> None:
        """Test returns True when user is authenticated."""
        mock_st.session_state = {"authenticated": True}

        from entra_id_auth_example.handlers import is_authenticated

        assert is_authenticated() is True

    @patch("entra_id_auth_example.handlers.st")
    def test_authenticated_false(self, mock_st: MagicMock) -> None:
        """Test returns False when user is not authenticated."""
        mock_st.session_state = {"authenticated": False}

        from entra_id_auth_example.handlers import is_authenticated

        assert is_authenticated() is False

    @patch("entra_id_auth_example.handlers.st")
    def test_authenticated_missing(self, mock_st: MagicMock) -> None:
        """Test returns False when session state is empty."""
        mock_st.session_state = {}

        from entra_id_auth_example.handlers import is_authenticated

        assert is_authenticated() is False


class TestGetCurrentUser:
    """Tests for get_current_user function."""

    @patch("entra_id_auth_example.handlers.st")
    def test_get_user_authenticated(self, mock_st: MagicMock) -> None:
        """Test returns user info when authenticated."""
        user_info = {"id": "user-123", "name": "Test User", "email": "test@example.com"}
        mock_st.session_state = {"authenticated": True, "user": user_info}

        from entra_id_auth_example.handlers import get_current_user

        result = get_current_user()
        assert result == user_info

    @patch("entra_id_auth_example.handlers.st")
    def test_get_user_not_authenticated(self, mock_st: MagicMock) -> None:
        """Test returns None when not authenticated."""
        mock_st.session_state = {"authenticated": False}

        from entra_id_auth_example.handlers import get_current_user

        assert get_current_user() is None


class TestGetTokenClaims:
    """Tests for get_token_claims function."""

    @patch("entra_id_auth_example.handlers.st")
    def test_get_claims_authenticated(self, mock_st: MagicMock) -> None:
        """Test returns claims when authenticated."""
        claims = {"sub": "user-123", "iss": "https://login.example.com"}
        mock_st.session_state = {"authenticated": True, "token_claims": claims}

        from entra_id_auth_example.handlers import get_token_claims

        result = get_token_claims()
        assert result == claims

    @patch("entra_id_auth_example.handlers.st")
    def test_get_claims_not_authenticated(self, mock_st: MagicMock) -> None:
        """Test returns None when not authenticated."""
        mock_st.session_state = {"authenticated": False}

        from entra_id_auth_example.handlers import get_token_claims

        assert get_token_claims() is None


class TestHandleCallback:
    """Tests for handle_callback function."""

    @patch("entra_id_auth_example.handlers._get_client")
    @patch("entra_id_auth_example.handlers.st")
    def test_no_code_in_query(self, mock_st: MagicMock, mock_get_client: MagicMock) -> None:
        """Test returns False when no code in query params."""
        mock_st.query_params = {}

        from entra_id_auth_example.handlers import handle_callback

        assert handle_callback() is False

    @patch("entra_id_auth_example.handlers._get_client")
    @patch("entra_id_auth_example.handlers.st")
    def test_invalid_state(self, mock_st: MagicMock, mock_get_client: MagicMock) -> None:
        """Test returns False when state is invalid."""
        mock_st.query_params = {"code": "auth-code", "state": "wrong-state"}
        mock_st.session_state = {"auth_state": "expected-state"}

        from entra_id_auth_example.handlers import handle_callback

        result = handle_callback()
        assert result is False
        mock_st.error.assert_called_once()

    @patch("entra_id_auth_example.handlers._get_client")
    @patch("entra_id_auth_example.handlers.st")
    def test_token_error(self, mock_st: MagicMock, mock_get_client: MagicMock) -> None:
        """Test returns False when token acquisition fails."""
        mock_query_params = MagicMock()
        mock_query_params.__contains__ = lambda self, k: k in {"code", "state"}
        mock_query_params.get = lambda k: {"code": "auth-code", "state": "test-state"}.get(k)
        mock_st.query_params = mock_query_params
        mock_st.session_state = {"auth_state": "test-state"}

        mock_client = MagicMock()
        mock_client.acquire_token_by_code.return_value = {
            "error": "invalid_grant",
            "error_description": "Code expired",
        }
        mock_get_client.return_value = mock_client

        from entra_id_auth_example.handlers import handle_callback

        result = handle_callback()
        assert result is False
        mock_st.error.assert_called()

    @patch("entra_id_auth_example.handlers._get_client")
    @patch("entra_id_auth_example.handlers.st")
    def test_successful_callback(self, mock_st: MagicMock, mock_get_client: MagicMock) -> None:
        """Test successful callback handling."""
        mock_query_params = MagicMock()
        mock_query_params.__contains__ = lambda self, k: k in {"code", "state"}
        mock_query_params.get = lambda k: {"code": "auth-code", "state": "test-state"}.get(k)
        mock_st.query_params = mock_query_params
        mock_st.session_state = {"auth_state": "test-state"}

        mock_client = MagicMock()
        mock_client.acquire_token_by_code.return_value = {
            "id_token_claims": {
                "sub": "user-123",
                "name": "Test User",
                "email": "test@example.com",
            }
        }
        mock_get_client.return_value = mock_client

        from entra_id_auth_example.handlers import handle_callback

        result = handle_callback()
        assert result is True
        assert mock_st.session_state["authenticated"] is True
        assert mock_st.session_state["user"]["id"] == "user-123"


class TestRequireAuth:
    """Tests for require_auth function."""

    @patch("entra_id_auth_example.handlers.st")
    def test_authenticated_passes(self, mock_st: MagicMock) -> None:
        """Test does not stop when authenticated."""
        mock_st.session_state = {"authenticated": True}

        from entra_id_auth_example.handlers import require_auth

        # Should not raise or call st.stop()
        require_auth()
        mock_st.stop.assert_not_called()

    @patch("entra_id_auth_example.handlers.st")
    def test_not_authenticated_stops(self, mock_st: MagicMock) -> None:
        """Test calls st.stop() when not authenticated."""
        mock_st.session_state = {"authenticated": False}
        mock_st.button.return_value = False

        from entra_id_auth_example.handlers import require_auth

        require_auth()
        mock_st.error.assert_called_once()
        mock_st.stop.assert_called_once()
