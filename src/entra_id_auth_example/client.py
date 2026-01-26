"""Entra ID認証用のMSALクライアントラッパー。"""

from __future__ import annotations

import ssl
from typing import Any

import requests
from msal import ConfidentialClientApplication  # type: ignore[import-untyped]
from requests.adapters import HTTPAdapter

from .config import AuthConfig


def _create_ssl_context(ca_file: str) -> ssl.SSLContext:
    """カスタムCA証明書を使用するSSLコンテキストを作成する。

    Python 3.13のssl.create_default_context()はVERIFY_X509_STRICTフラグを
    デフォルトで有効にする。AKI拡張のないCA証明書（企業プロキシ等）を
    使用する場合、このフラグを無効化する必要がある。

    Args:
        ca_file: CA証明書ファイルのパス。
    """
    ctx = ssl.create_default_context()
    ctx.load_verify_locations(cafile=ca_file)
    ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return ctx


def _create_http_client(ca_file: str) -> requests.Session:
    """カスタムCA証明書を使用するHTTPクライアントを作成する。

    Args:
        ca_file: CA証明書ファイルのパス。
    """
    ctx = _create_ssl_context(ca_file)

    class _SSLAdapter(HTTPAdapter):
        def init_poolmanager(
            self, connections: int, maxsize: int, block: bool = False, **kwargs: Any
        ) -> None:
            kwargs["ssl_context"] = ctx
            super().init_poolmanager(connections, maxsize, block, **kwargs)  # type: ignore[no-untyped-call]

        def build_connection_pool_key_attributes(
            self,
            request: requests.PreparedRequest,
            verify: bool | str,
            cert: tuple[str, str] | str | None = None,
        ) -> Any:
            host_params, pool_kwargs = super().build_connection_pool_key_attributes(
                request, verify, cert
            )
            pool_kwargs["ssl_context"] = ctx
            return host_params, pool_kwargs

    session = requests.Session()
    session.mount("https://", _SSLAdapter())
    return session


class EntraAuthClient:
    """MSALを使用したMicrosoft Entra ID認証クライアント。

    MSALのConfidentialClientApplicationをラップし、
    OIDC認証フローのシンプルなインターフェースを提供する。
    """

    SCOPES = ["email"]

    def __init__(self, config: AuthConfig) -> None:
        """Entra ID認証クライアントを初期化する。

        Args:
            config: 認証設定。
        """
        self._config = config
        kwargs: dict[str, Any] = {}
        if config.ssl_ca_file:
            kwargs["http_client"] = _create_http_client(config.ssl_ca_file)
        self._app = ConfidentialClientApplication(
            client_id=config.client_id,
            client_credential=config.client_secret,
            authority=config.authority,
            **kwargs,
        )

    def get_auth_url(self, state: str) -> str:
        """ログイン用の認可URLを生成する。

        Args:
            state: CSRF対策用のstateパラメータ。

        Returns:
            ユーザーをリダイレクトする認可URL。
        """
        result: str = self._app.get_authorization_request_url(
            scopes=self.SCOPES,
            state=state,
            redirect_uri=self._config.redirect_uri,
        )
        return result

    def acquire_token_by_code(self, code: str) -> dict[str, Any]:
        """認可コードをトークンに交換する。

        MSALは自動的にIDトークンの検証を行う:
        - 署名検証（ディスカバリエンドポイントのJWKSを使用）
        - 発行者（iss）の検証（設定されたauthorityと照合）
        - 対象者（aud）の検証（client_idと照合）
        - 有効期限（exp）、nbf、iat の検証

        Args:
            code: コールバックで受け取った認可コード。

        Returns:
            id_token、access_token、claimsを含むトークンレスポンス。
            成功時は検証済みのclaimsを含む'id_token_claims'が含まれる。
            エラー時は'error'と'error_description'キーが含まれる。
        """
        result: dict[str, Any] = self._app.acquire_token_by_authorization_code(
            code=code,
            scopes=self.SCOPES,
            redirect_uri=self._config.redirect_uri,
        )
        return result

    @property
    def logout_url(self) -> str:
        """Entra IDのログアウトURLを返す。

        Returns:
            ログアウトURL。
        """
        return self._config.logout_url
