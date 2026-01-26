"""Entra ID認証を使用したメインStreamlitアプリケーション。"""

import streamlit as st

from entra_id_auth_example import (
    get_current_user,
    handle_callback,
    is_authenticated,
    login,
    logout,
    render_sidebar_account,
    render_site_header,
)

st.set_page_config(
    page_title="Streamlit Entra ID Auth Example",
    page_icon="🔐",
    layout="centered",
)


def main() -> None:
    """メインアプリケーションのエントリーポイント。"""
    # OAuthコールバックを処理
    handle_callback()

    # サイドバーアカウントを表示
    render_sidebar_account()

    # サイトヘッダー
    render_site_header()

    if is_authenticated():
        _show_authenticated_view()
    else:
        _show_login_view()


def _show_authenticated_view() -> None:
    """認証済みユーザーのビューを表示する。"""
    user = get_current_user()
    if user is None:
        return

    st.success(f"ようこそ、{user['name']}さん！")

    with st.container():
        st.subheader("ユーザー情報")
        col1, col2 = st.columns(2)
        with col1:
            st.text("ID")
            st.code(user["id"])
        with col2:
            st.text("Email")
            st.code(user["email"])

    st.divider()

    if st.button("ログアウト", type="primary"):
        logout()


def _show_login_view() -> None:
    """未認証ユーザーのログインビューを表示する。"""
    st.info("このアプリケーションを使用するにはログインが必要です。")

    if st.button("Microsoft アカウントでログイン", type="primary"):
        login()


if __name__ == "__main__":
    main()
