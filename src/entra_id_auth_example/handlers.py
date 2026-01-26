"""Entra ID用のStreamlit認証ハンドラー。"""

from __future__ import annotations

import secrets
from typing import Any, TypedDict, cast

import streamlit as st

from .client import EntraAuthClient
from .config import load_config


class UserInfo(TypedDict):
    """IDトークンのclaimsから抽出したユーザー情報。"""

    id: str
    name: str
    email: str


# セッションステートのキー
_AUTH_STATE_KEY = "auth_state"
_AUTHENTICATED_KEY = "authenticated"
_USER_KEY = "user"
_TOKEN_CLAIMS_KEY = "token_claims"


def _get_client() -> EntraAuthClient:
    """認証クライアントを取得または作成する。"""
    if "auth_client" not in st.session_state:
        config = load_config()
        st.session_state["auth_client"] = EntraAuthClient(config)
    return cast(EntraAuthClient, st.session_state["auth_client"])


def login() -> None:
    """Entra IDにリダイレクトして認証フローを開始する。

    CSRFトークンを生成し、ユーザーをEntra IDログインページにリダイレクトする。
    """
    client = _get_client()

    # CSRFステートトークンを生成
    state = secrets.token_urlsafe(32)
    st.session_state[_AUTH_STATE_KEY] = state

    # 認可URLを取得してリダイレクト
    auth_url = client.get_auth_url(state)
    st.markdown(
        f'<meta http-equiv="refresh" content="0;url={auth_url}">',
        unsafe_allow_html=True,
    )
    st.stop()


def logout() -> None:
    """セッションをクリアしてEntra IDのログアウトにリダイレクトする。

    認証関連のセッションステートをすべてクリアし、
    Entra IDのログアウトエンドポイントにリダイレクトする。
    """
    client = _get_client()
    logout_url = client.logout_url

    # セッションステートをクリア
    for key in [_AUTHENTICATED_KEY, _USER_KEY, _TOKEN_CLAIMS_KEY, _AUTH_STATE_KEY]:
        if key in st.session_state:
            del st.session_state[key]

    # ログアウトURLにリダイレクト
    st.markdown(
        f'<meta http-equiv="refresh" content="0;url={logout_url}">',
        unsafe_allow_html=True,
    )
    st.stop()


def handle_callback() -> bool:
    """OAuthコールバックを処理し、認可コードをトークンに交換する。

    クエリパラメータの認可コードを確認し、stateパラメータを検証して、
    認可コードをトークンに交換する。

    Returns:
        認証が成功した場合はTrue、それ以外はFalse。
    """
    query_params = st.query_params

    # コールバックリクエストかどうかを確認
    if "code" not in query_params:
        return False

    code = query_params.get("code")
    state = query_params.get("state")

    # codeが存在することを確認（前のチェックで常にtrueのはず）
    if code is None:
        return False

    # CSRF防止のためstateを検証
    expected_state = st.session_state.get(_AUTH_STATE_KEY)
    if not expected_state or state != expected_state:
        st.error("Invalid state parameter. Please try logging in again.")
        return False

    # 検証後にstateをクリア
    del st.session_state[_AUTH_STATE_KEY]

    # 認可コードをトークンに交換
    client = _get_client()
    result = client.acquire_token_by_code(code)

    if "error" in result:
        error_desc = result.get("error_description", result.get("error", "Unknown error"))
        st.error(f"Authentication failed: {error_desc}")
        return False

    # IDトークンのclaimsからユーザー情報を抽出
    claims = result.get("id_token_claims", {})
    user_info: UserInfo = {
        "id": claims.get("sub", ""),
        "name": claims.get("name", ""),
        "email": claims.get("email") or claims.get("preferred_username", ""),
    }

    # セッションステートに保存
    st.session_state[_AUTHENTICATED_KEY] = True
    st.session_state[_USER_KEY] = user_info
    st.session_state[_TOKEN_CLAIMS_KEY] = claims

    # URLをクリーンアップするためクエリパラメータをクリア
    st.query_params.clear()

    return True


def is_authenticated() -> bool:
    """現在のユーザーが認証済みかどうかを確認する。

    Returns:
        ユーザーが認証済みの場合はTrue、それ以外はFalse。
    """
    return bool(st.session_state.get(_AUTHENTICATED_KEY, False))


def get_current_user() -> UserInfo | None:
    """現在の認証済みユーザーの情報を取得する。

    Returns:
        id、name、emailを含むユーザー情報辞書。
        ユーザーが認証されていない場合はNone。
    """
    if not is_authenticated():
        return None
    return st.session_state.get(_USER_KEY)


def require_auth() -> None:
    """認証を必須とするガード関数。

    ユーザーが認証されていない場合、エラーメッセージとログインボタンを表示し、
    Streamlitスクリプトの実行を停止する。
    """
    if not is_authenticated():
        st.error("このページは認証が必要です。ログインしてください。")
        if st.button("Microsoft アカウントでログイン", type="primary"):
            login()
        st.stop()


def get_token_claims() -> dict[str, Any] | None:
    """生のIDトークンclaimsを取得する。

    claimsはMSALによって検証済み:
    - JWKSを使用した署名検証
    - authorityに対する発行者（iss）の検証
    - client_idに対する対象者（aud）の検証
    - 有効期限（exp）、nbf、iatの検証

    Returns:
        sub、name、email、iss、aud、expなどを含む生のIDトークンclaims。
        ユーザーが認証されていない場合はNone。
    """
    if not is_authenticated():
        return None
    return st.session_state.get(_TOKEN_CLAIMS_KEY)


_SITE_TITLE = "🔐 Entra ID Auth"


def render_site_header() -> None:
    """サイトヘッダーをタイトルとAboutリンク付きで表示する。

    ブラウザ幅いっぱいに広がるChatGPTスタイルのヘッダーバーを表示:
    - 左: ホームへのリンク付きサイトタイトル
    - 右: ?アイコンのAboutリンク
    """
    st.markdown(
        f"""
        <style>
            .site-header-container {{
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 999;
                background: var(--background-color, white);
                border-bottom: 1px solid rgba(128, 128, 128, 0.2);
            }}
            .site-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.75rem 1.5rem;
                max-width: 100%;
            }}
            .site-header a {{
                text-decoration: none;
                color: inherit;
            }}
            .site-title {{
                font-size: 1.2rem;
                font-weight: 600;
                margin: 0;
            }}
            .about-link {{
                width: 28px;
                height: 28px;
                border-radius: 50%;
                border: 1px solid rgba(128, 128, 128, 0.3);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                color: #666;
            }}
            .about-link:hover {{
                background: rgba(128, 128, 128, 0.1);
            }}
            /* 固定ヘッダーのためメインコンテンツにパディングを追加 */
            .stMainBlockContainer {{
                padding-top: 4rem !important;
            }}
        </style>
        <div class="site-header-container">
            <div class="site-header">
                <a href="/" target="_self">
                    <div class="site-title">{_SITE_TITLE}</div>
                </a>
                <a href="/about" target="_self">
                    <div class="about-link">?</div>
                </a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _get_initials(name: str) -> str:
    """名前からイニシャルを抽出する。

    Args:
        name: ユーザーのフルネーム。

    Returns:
        最大2文字のイニシャル（例: "John Doe" -> "JD"）。
    """
    if not name:
        return "?"
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return parts[0][0].upper()


def render_sidebar_account() -> None:
    """サイドバーの下部にユーザーアカウント情報を表示する。

    認証済みの場合: サイドバー下部にユーザーアバター（イニシャル）、名前、
    ログアウトボタンを表示。
    未認証の場合: サイドバーを完全に非表示にする。
    """
    if not is_authenticated():
        # 未認証時はサイドバーを非表示
        st.markdown(
            """
            <style>
                [data-testid="stSidebar"] { display: none; }
                [data-testid="stSidebarCollapsedControl"] { display: none; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        return

    user = get_current_user()
    if not user:
        return

    # サイドバー下部にアカウント情報を配置するCSS
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] > div:first-child {
                display: flex;
                flex-direction: column;
                height: 100vh;
            }
            [data-testid="stSidebar"] > div:first-child > div:first-child {
                flex: 1;
            }
            .sidebar-account {
                padding: 1rem;
                border-top: 1px solid rgba(128, 128, 128, 0.2);
                margin-top: auto;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        # 下部にコンテンツを押し下げるスペーサー
        st.markdown('<div style="flex: 1;"></div>', unsafe_allow_html=True)

        initials = _get_initials(user["name"])

        # イニシャル付きアバターとユーザー名
        name_style = (
            "font-weight: 500; font-size: 14px; "
            "overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"
        )
        email_style = (
            "font-size: 12px; color: #888; "
            "overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"
        )
        avatar_style = (
            "width: 36px; height: 36px; border-radius: 50%; "
            "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); "
            "display: flex; align-items: center; justify-content: center; "
            "color: white; font-weight: bold; font-size: 14px;"
        )
        container_style = (
            "display: flex; align-items: center; gap: 12px; padding: 8px 0;"
        )

        st.markdown("---")
        st.markdown(
            f"""
            <div style="{container_style}">
                <div style="{avatar_style}">{initials}</div>
                <div style="flex: 1; min-width: 0;">
                    <div style="{name_style}">{user['name']}</div>
                    <div style="{email_style}">{user['email']}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("ログアウト", key="sidebar_logout", use_container_width=True):
            logout()
