"""Entra ID認証の設定管理モジュール。"""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlencode

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
    """

    client_id: str
    client_secret: str
    tenant_id: str
    redirect_uri: str
    ssl_ca_file: str | None = None

    @property
    def authority(self) -> str:
        """テナントのauthority URLを返す。"""
        return f"https://login.microsoftonline.com/{self.tenant_id}"

    @property
    def base_url(self) -> str:
        """アプリケーションのベースURL（パスなし）を返す。"""
        from urllib.parse import urlparse

        parsed = urlparse(self.redirect_uri)
        return f"{parsed.scheme}://{parsed.netloc}/"

    @property
    def logout_url(self) -> str:
        """Entra IDのログアウトURLを返す。

        ログアウト後、ユーザーはアプリケーションのベースURLにリダイレクトされる。
        """
        base_logout_url = f"{self.authority}/oauth2/v2.0/logout"
        params = urlencode({"post_logout_redirect_uri": self.base_url})
        return f"{base_logout_url}?{params}"


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
    ssl_ca_file = values.get("SSL_CA_FILE") or None

    missing: list[str] = []
    if not client_id:
        missing.append("AZURE_CLIENT_ID")
    if not client_secret:
        missing.append("AZURE_CLIENT_SECRET")
    if not tenant_id:
        missing.append("AZURE_TENANT_ID")

    if missing:
        raise ValueError(f"Missing required configuration: {', '.join(missing)}")

    # この時点で必須値はすべてNoneではないことが確認済み
    assert client_id is not None
    assert client_secret is not None
    assert tenant_id is not None

    return AuthConfig(
        client_id=client_id,
        client_secret=client_secret,
        tenant_id=tenant_id,
        redirect_uri=redirect_uri,
        ssl_ca_file=ssl_ca_file,
    )
