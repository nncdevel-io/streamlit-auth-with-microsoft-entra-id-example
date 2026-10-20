"""Tests for callback module."""

import asyncio

from starlette.requests import Request
from starlette.routing import Route

from entra_id_auth_example.callback import create_callback_routes


def _call(route: Route, query: bytes) -> tuple[int, str]:
    """Call the route endpoint with a GET request and return (status, location)."""
    scope = {
        "type": "http",
        "method": "GET",
        "scheme": "http",
        "server": ("localhost", 8501),
        "path": route.path,
        "query_string": query,
        "headers": [],
    }
    response = asyncio.run(route.endpoint(Request(scope)))
    return response.status_code, response.headers["location"]


class TestCreateCallbackRoutes:
    """Tests for create_callback_routes function."""

    def test_route_uses_redirect_uri_path(self) -> None:
        """Test the route is registered at the path of redirect_uri."""
        routes = create_callback_routes("http://localhost:8501/callback")

        assert [route.path for route in routes] == ["/callback"]

    def test_forwards_query_to_streamlit_callback(self) -> None:
        """Test /callback redirects to /oauth2callback keeping the query string."""
        (route,) = create_callback_routes("http://localhost:8501/callback")

        assert _call(route, b"code=abc&state=xyz") == (307, "/oauth2callback?code=abc&state=xyz")

    def test_forwards_without_query(self) -> None:
        """Test /callback without query redirects to /oauth2callback."""
        (route,) = create_callback_routes("http://localhost:8501/callback")

        assert _call(route, b"") == (307, "/oauth2callback")

    def test_no_route_for_streamlit_callback_path(self) -> None:
        """Test no route is added when redirect_uri already uses /oauth2callback."""
        assert create_callback_routes("http://localhost:8501/oauth2callback") == []
