"""Entra ID認証を使用したメインStreamlitアプリケーション。"""

import logging

import streamlit as st

from entra_id_auth_example import (
    handle_callback,
    render_sidebar_account,
    render_site_header,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

st.set_page_config(
    page_title="Streamlit Entra ID Auth Example",
    page_icon="🔐",
    layout="centered",
)

# OAuthコールバック処理（navigation設定前に実行）
# Entra IDからのリダイレクト（?code=...&state=...）を受け取り、トークン交換を行う
if "code" in st.query_params:
    if handle_callback():
        st.rerun()
    else:
        if st.button("トップページへ", type="primary"):
            st.query_params.clear()
            st.rerun()
        st.stop()

# 共通レイアウト
render_sidebar_account()
render_site_header()

# ページ定義
pg = st.navigation(
    [
        st.Page("pages/home.py", title="Home", default=True, icon="🏠"),
        st.Page("pages/about.py", title="About", icon="ℹ️"),
        st.Page("pages/dashboard.py", title="Dashboard", icon="📊"),
        st.Page("pages/profile.py", title="Profile", icon="👤"),
    ]
)

pg.run()
