"""Entra ID認証用のMSALクライアントラッパー。"""

from __future__ import annotations

from typing import Any

from msal import ConfidentialClientApplication  # type: ignore[import-untyped]

from .config import AuthConfig


class EntraAuthClient:
    """MSALを使用したMicrosoft Entra ID認証クライアント。

    MSALのConfidentialClientApplicationをラップし、
    OIDC認証フローのシンプルなインターフェースを提供する。
    """

    SCOPES = ["openid", "profile", "email"]

    def __init__(self, config: AuthConfig) -> None:
        """Entra ID認証クライアントを初期化する。

        Args:
            config: 認証設定。
        """
        self._config = config
        self._app = ConfidentialClientApplication(
            client_id=config.client_id,
            client_credential=config.client_secret,
            authority=config.authority,
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
