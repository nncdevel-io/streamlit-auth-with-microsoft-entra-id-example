"""Streamlit Entra ID 認証パッケージ。

Microsoft Entra ID（旧Azure AD）を使用したStreamlitアプリケーション向けの
認証ユーティリティを提供します。
"""

from .client import EntraAuthClient
from .config import AuthConfig, load_config
from .handlers import (
    get_current_user,
    get_token_claims,
    handle_callback,
    is_authenticated,
    login,
    logout,
    render_sidebar_account,
    render_site_header,
    require_auth,
)

__all__ = [
    "AuthConfig",
    "EntraAuthClient",
    "get_current_user",
    "get_token_claims",
    "handle_callback",
    "is_authenticated",
    "load_config",
    "login",
    "logout",
    "render_sidebar_account",
    "render_site_header",
    "require_auth",
]
