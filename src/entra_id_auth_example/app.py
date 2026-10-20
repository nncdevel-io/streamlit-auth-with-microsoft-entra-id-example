"""Entra ID認証を使用したメインStreamlitアプリケーション。"""

import logging

import streamlit as st

from entra_id_auth_example import (
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
