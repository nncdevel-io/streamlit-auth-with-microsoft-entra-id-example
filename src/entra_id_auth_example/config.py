"""Entra ID認証の設定管理モジュール。"""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from dotenv import dotenv_values

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthConfig:
    """Microsoft Entra IDの認証設定。

    Attributes:
        client_id: Azure Portalのアプリケーション（クライアント）ID。
        client_secret: 証明書とシークレットのクライアントシークレット。
        tenant_id: ディレクトリ（テナント）ID。
        redirect_uri: アプリ登録で設定したリダイレクトURI。
        cookie_secret: Streamlitが認証Cookieの署名に使うシークレット。
        ssl_ca_file: Entra IDとのHTTPS通信で信頼するCA証明書ファイルのパス。
    """

    client_id: str
    client_secret: str
    tenant_id: str
    redirect_uri: str
    cookie_secret: str
    ssl_ca_file: str | None = None

    @property
    def authority(self) -> str:
        """テナントのauthority URLを返す。"""
        return f"https://login.microsoftonline.com/{self.tenant_id}"

    @property
    def server_metadata_url(self) -> str:
        """テナントのOIDCメタデータのURLを返す。"""
        return f"{self.authority}/v2.0/.well-known/openid-configuration"

    def to_streamlit_secrets(self) -> dict[str, Any]:
        """st.login()が読み込む形式のsecretsを返す。

        st.App(secrets=...)に渡し、st.secrets["auth"]として参照させる。
        SSL_CA_FILEを指定した場合は、AuthlibがEntra IDとの通信に使うhttpxへ
        verifyとして渡す。
        """
        auth: dict[str, Any] = {
            "redirect_uri": self.redirect_uri,
            "cookie_secret": self.cookie_secret,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "server_metadata_url": self.server_metadata_url,
        }
        if self.ssl_ca_file:
            auth["client_kwargs"] = {"verify": self.ssl_ca_file}
        return {"auth": auth}


def _get_config_values() -> Mapping[str, str | None]:
    """環境に応じた設定値を取得する。

    本番環境（ENV=production）: 環境変数からのみ読み込む。
    開発環境: .envファイルからのみ読み込む（環境変数は無視）。
    """
    if os.getenv("ENV") == "production":
        logger.info("Loading config from environment variables (production mode)")
        return os.environ
    logger.info("Loading config from .env file (development mode)")
    return dotenv_values(".env")


def load_config() -> AuthConfig:
    """認証設定を読み込む。

    本番環境（ENV=production）: 環境変数から読み込む。
    開発環境: .envファイルからのみ読み込む。

    Returns:
        環境から読み込んだ認証設定。

    Raises:
        ValueError: 必須の設定値が設定されていない場合。
    """
    values = _get_config_values()

    client_id = values.get("AZURE_CLIENT_ID")
    client_secret = values.get("AZURE_CLIENT_SECRET")
    tenant_id = values.get("AZURE_TENANT_ID")
    redirect_uri = values.get("AZURE_REDIRECT_URI") or "http://localhost:8501/callback"
    cookie_secret = values.get("AUTH_COOKIE_SECRET")
    ssl_ca_file = values.get("SSL_CA_FILE") or None

    missing: list[str] = []
    if not client_id:
        missing.append("AZURE_CLIENT_ID")
    if not client_secret:
        missing.append("AZURE_CLIENT_SECRET")
    if not tenant_id:
        missing.append("AZURE_TENANT_ID")
    if not cookie_secret:
        missing.append("AUTH_COOKIE_SECRET")

    if missing:
        raise ValueError(f"Missing required configuration: {', '.join(missing)}")

    # この時点で必須値はすべてNoneではないことが確認済み
    assert client_id is not None
    assert client_secret is not None
    assert tenant_id is not None
    assert cookie_secret is not None

    return AuthConfig(
        client_id=client_id,
        client_secret=client_secret,
        tenant_id=tenant_id,
        redirect_uri=redirect_uri,
        cookie_secret=cookie_secret,
        ssl_ca_file=ssl_ca_file,
    )
