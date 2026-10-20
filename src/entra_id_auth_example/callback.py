"""Entra IDのリダイレクト先をst.login()のコールバックへ転送するルート。

st.login()のコールバックのパスは/oauth2callbackに固定されている。Entra IDのアプリ登録で
別のパス（例: /callback）を登録している場合に、そのパスで受けたリクエストを転送する。
トークン交換で送るredirect_uriは、ログイン開始時に使った値（登録済みのパス）のまま変わらない。
"""

from __future__ import annotations

from urllib.parse import urlparse

from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.routing import Route

# st.login()がコールバックを受け付けるパス
STREAMLIT_CALLBACK_PATH = "/oauth2callback"


async def _forward_to_streamlit_callback(request: Request) -> RedirectResponse:
    """クエリパラメータ（code、state など）を付けたまま/oauth2callbackへリダイレクトする。"""
    url = STREAMLIT_CALLBACK_PATH
    if request.url.query:
        url = f"{url}?{request.url.query}"
    return RedirectResponse(url, status_code=307)


def create_callback_routes(redirect_uri: str) -> list[Route]:
    """redirect_uriのパスを/oauth2callbackへ転送するルートを作成する。

    Args:
        redirect_uri: Entra IDのアプリ登録で設定したリダイレクトURI。

    Returns:
        転送用のルート。パスが/oauth2callbackの場合は転送不要のため空のリスト。
    """
    path = urlparse(redirect_uri).path or "/"
    if path == STREAMLIT_CALLBACK_PATH:
        return []
    return [Route(path, _forward_to_streamlit_callback, methods=["GET"])]
