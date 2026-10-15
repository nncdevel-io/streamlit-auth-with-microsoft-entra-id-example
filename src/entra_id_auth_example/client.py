"""Entra ID認証用のMSALクライアントラッパー。"""

from __future__ import annotations

import hmac
import ssl
from typing import Any

import jwt
import requests
from msal import ConfidentialClientApplication  # type: ignore[import-untyped]
from requests.adapters import HTTPAdapter

from .config import AuthConfig

# 外部へのHTTP通信（OIDCメタデータ・JWKSの取得）のタイムアウト秒数
_HTTP_TIMEOUT_SECONDS = 10
# IDトークンの時刻クレーム（exp、nbf、iat）の検証で許容する時計のずれ
_CLOCK_SKEW_SECONDS = 120


class IdTokenValidationError(Exception):
    """IDトークンの検証に失敗したことを表す例外。"""


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


def _create_http_client(ctx: ssl.SSLContext) -> requests.Session:
    """指定したSSLコンテキストを使用するHTTPクライアントを作成する。

    Args:
        ctx: HTTPS接続に使用するSSLコンテキスト。
    """

    class _SSLAdapter(HTTPAdapter):
        def init_poolmanager(
            self, connections: int, maxsize: int, block: bool = False, **kwargs: Any
        ) -> None:
            kwargs["ssl_context"] = ctx
            super().init_poolmanager(connections, maxsize, block, **kwargs)

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
        self._ssl_context: ssl.SSLContext | None = None
        self._http = requests.Session()
        if config.ssl_ca_file:
            self._ssl_context = _create_ssl_context(config.ssl_ca_file)
            self._http = _create_http_client(self._ssl_context)
            kwargs["http_client"] = self._http
        self._issuer: str | None = None
        self._jwks_client: jwt.PyJWKClient | None = None
        self._app = ConfidentialClientApplication(
            client_id=config.client_id,
            client_credential=config.client_secret,
            authority=config.authority,
            **kwargs,
        )

    def get_auth_url(self, state: str, nonce: str) -> str:
        """ログイン用の認可URLを生成する。

        Args:
            state: CSRF対策用のstateパラメータ。
            nonce: IDトークンに埋め込ませるnonce。トークン交換時の検証に使う。

        Returns:
            ユーザーをリダイレクトする認可URL。
        """
        result: str = self._app.get_authorization_request_url(
            scopes=self.SCOPES,
            state=state,
            redirect_uri=self._config.redirect_uri,
            nonce=nonce,
        )
        return result

    def acquire_token_by_code(self, code: str, nonce: str) -> dict[str, Any]:
        """認可コードをトークンに交換し、IDトークンを検証する。

        MSAL 1.38.0以降はIDトークンを検証しないため、validate_id_token()で検証し、
        'id_token_claims'を検証済みのclaimsで置き換える。

        Args:
            code: コールバックで受け取った認可コード。
            nonce: 認可リクエストで送ったnonce。

        Returns:
            id_token、access_token、claimsを含むトークンレスポンス。
            成功時は検証済みのclaimsを含む'id_token_claims'が含まれる。
            エラー時（IDトークンの検証失敗を含む）は'error'と'error_description'キーが含まれる。
        """
        result: dict[str, Any] = self._app.acquire_token_by_authorization_code(
            code=code,
            scopes=self.SCOPES,
            redirect_uri=self._config.redirect_uri,
        )
        if "error" in result:
            return result

        id_token = result.get("id_token")
        if not id_token:
            return {
                "error": "invalid_id_token",
                "error_description": "The token response does not contain an ID token.",
            }
        try:
            result["id_token_claims"] = self.validate_id_token(id_token, nonce)
        except IdTokenValidationError as e:
            return {
                "error": "invalid_id_token",
                "error_description": f"ID token validation failed: {e}",
            }
        return result

    def validate_id_token(self, id_token: str, nonce: str) -> dict[str, Any]:
        """IDトークンの署名とclaimsを検証する。

        検証する項目:
        - 署名（OIDCメタデータのjwks_uriから取得した公開鍵、RS256）
        - 発行者（iss）がOIDCメタデータのissuerと一致すること
        - 対象者（aud）がclient_idと一致すること
        - 有効期限（exp）、nbf、iat（時計のずれを_CLOCK_SKEW_SECONDS秒まで許容）
        - nonceが認可リクエストで送った値と一致すること

        authorityに"common"や"organizations"を使うとissuerにテナントIDのプレースホルダーが
        含まれ、発行者の検証は必ず失敗する。特定のテナントIDを設定する前提とする。

        Args:
            id_token: トークンレスポンスに含まれるIDトークン（JWT）。
            nonce: 認可リクエストで送ったnonce。

        Returns:
            検証済みのIDトークンclaims。

        Raises:
            IdTokenValidationError: メタデータや公開鍵を取得できない場合、または検証に失敗した場合。
        """
        try:
            issuer, jwks_client = self._load_oidc_metadata()
            signing_key = jwks_client.get_signing_key_from_jwt(id_token)
            claims: dict[str, Any] = jwt.decode(
                id_token,
                signing_key,
                algorithms=["RS256"],
                audience=self._config.client_id,
                issuer=issuer,
                leeway=_CLOCK_SKEW_SECONDS,
                options={"require": ["exp", "iat", "iss", "aud", "sub", "nonce"]},
            )
        except (requests.RequestException, KeyError, ValueError, jwt.PyJWTError) as e:
            raise IdTokenValidationError(str(e)) from e

        if not hmac.compare_digest(str(claims["nonce"]), nonce):
            raise IdTokenValidationError("nonce does not match")
        return claims

    def _load_oidc_metadata(self) -> tuple[str, jwt.PyJWKClient]:
        """OIDCメタデータを取得し、issuerとJWKSクライアントを返す。

        取得結果はインスタンスに保持する。PyJWKClientは未知のkidを受け取ると
        JWKSを再取得するため、署名鍵の更新にも追従する。

        Returns:
            (issuer, JWKSクライアント) のタプル。
        """
        if self._issuer is None or self._jwks_client is None:
            url = f"{self._config.authority}/v2.0/.well-known/openid-configuration"
            response = self._http.get(url, timeout=_HTTP_TIMEOUT_SECONDS)
            response.raise_for_status()
            metadata = response.json()
            self._jwks_client = jwt.PyJWKClient(
                metadata["jwks_uri"],
                timeout=_HTTP_TIMEOUT_SECONDS,
                ssl_context=self._ssl_context,
            )
            self._issuer = metadata["issuer"]
        return self._issuer, self._jwks_client

    @property
    def logout_url(self) -> str:
        """Entra IDのログアウトURLを返す。

        Returns:
            ログアウトURL。
        """
        return self._config.logout_url
