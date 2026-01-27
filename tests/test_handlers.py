"""Tests for handlers module."""

from unittest.mock import MagicMock, patch

_TEST_SECRET = "test-client-secret"


def _make_valid_state(secret: str = _TEST_SECRET) -> tuple[str, str]:
    """テスト用にHMAC署名付きstateを生成する。Returns (nonce, signed_state)."""
    from entra_id_auth_example.handlers import _create_signed_state

    return _create_signed_state(secret)


def _mock_config() -> MagicMock:
    """テスト用のAuthConfig mockを返す。"""
    config = MagicMock()
    config.client_secret = _TEST_SECRET
    config.redirect_uri = "http://localhost:8501/"
    return config


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


class TestSignedState:
    """Tests for _create_signed_state and _verify_state."""

    def test_create_and_verify(self) -> None:
        """Test that created state can be verified."""
        from entra_id_auth_example.handlers import _create_signed_state, _verify_state

        nonce, state = _create_signed_state(_TEST_SECRET)
        assert _verify_state(state, nonce, _TEST_SECRET) is True

    def test_wrong_cookie_nonce(self) -> None:
        """Test verification fails with wrong cookie nonce."""
        from entra_id_auth_example.handlers import _create_signed_state, _verify_state

        _, state = _create_signed_state(_TEST_SECRET)
        assert _verify_state(state, "wrong-nonce", _TEST_SECRET) is False

    def test_wrong_secret(self) -> None:
        """Test verification fails with wrong secret."""
        from entra_id_auth_example.handlers import _create_signed_state, _verify_state

        nonce, state = _create_signed_state(_TEST_SECRET)
        assert _verify_state(state, nonce, "wrong-secret") is False

    def test_tampered_state(self) -> None:
        """Test verification fails with tampered state."""
        from entra_id_auth_example.handlers import _create_signed_state, _verify_state

        nonce, state = _create_signed_state(_TEST_SECRET)
        tampered = "tampered." + state.rsplit(".", 1)[1]
        assert _verify_state(tampered, nonce, _TEST_SECRET) is False

    def test_no_cookie(self) -> None:
        """Test verification fails with no cookie."""
        from entra_id_auth_example.handlers import _create_signed_state, _verify_state

        _, state = _create_signed_state(_TEST_SECRET)
        assert _verify_state(state, None, _TEST_SECRET) is False

    def test_no_state(self) -> None:
        """Test verification fails with no state."""
        from entra_id_auth_example.handlers import _verify_state

        assert _verify_state(None, "some-nonce", _TEST_SECRET) is False

    def test_malformed_state(self) -> None:
        """Test verification fails with state without dot separator."""
        from entra_id_auth_example.handlers import _verify_state

        assert _verify_state("no-dot-separator", "nonce", _TEST_SECRET) is False


class TestHandleCallback:
    """Tests for handle_callback function."""

    @patch("entra_id_auth_example.handlers._get_client")
    @patch("entra_id_auth_example.handlers.st")
    def test_no_code_in_query(self, mock_st: MagicMock, mock_get_client: MagicMock) -> None:
        """Test returns False when no code in query params."""
        mock_st.query_params = {}

        from entra_id_auth_example.handlers import handle_callback

        assert handle_callback() is False

    @patch("entra_id_auth_example.handlers.load_config", return_value=_mock_config())
    @patch("entra_id_auth_example.handlers._get_client")
    @patch("entra_id_auth_example.handlers.st")
    def test_invalid_state(
        self, mock_st: MagicMock, mock_get_client: MagicMock, mock_load: MagicMock
    ) -> None:
        """Test returns False when state is invalid."""
        mock_st.query_params = {"code": "auth-code", "state": "wrong-state"}
        mock_st.session_state = {}
        mock_st.context.cookies = {}

        from entra_id_auth_example.handlers import handle_callback

        result = handle_callback()
        assert result is False
        mock_st.error.assert_called_once()

    @patch("entra_id_auth_example.handlers.components")
    @patch("entra_id_auth_example.handlers.load_config", return_value=_mock_config())
    @patch("entra_id_auth_example.handlers._get_client")
    @patch("entra_id_auth_example.handlers.st")
    def test_token_error(
        self,
        mock_st: MagicMock,
        mock_get_client: MagicMock,
        mock_load: MagicMock,
        mock_components: MagicMock,
    ) -> None:
        """Test returns False when token acquisition fails."""
        nonce, signed_state = _make_valid_state()
        mock_query_params = MagicMock()
        mock_query_params.__contains__ = lambda self, k: k in {"code", "state"}
        mock_query_params.get = lambda k: {"code": "auth-code", "state": signed_state}.get(k)
        mock_st.query_params = mock_query_params
        mock_st.session_state = {}
        mock_st.context.cookies = {"oauth_state": nonce}

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

    @patch("entra_id_auth_example.handlers.components")
    @patch("entra_id_auth_example.handlers.load_config", return_value=_mock_config())
    @patch("entra_id_auth_example.handlers._get_client")
    @patch("entra_id_auth_example.handlers.st")
    def test_successful_callback(
        self,
        mock_st: MagicMock,
        mock_get_client: MagicMock,
        mock_load: MagicMock,
        mock_components: MagicMock,
    ) -> None:
        """Test successful callback handling."""
        nonce, signed_state = _make_valid_state()
        mock_query_params = MagicMock()
        mock_query_params.__contains__ = lambda self, k: k in {"code", "state"}
        mock_query_params.get = lambda k: {"code": "auth-code", "state": signed_state}.get(k)
        mock_st.query_params = mock_query_params
        mock_st.session_state = {}
        mock_st.context.cookies = {"oauth_state": nonce}

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
