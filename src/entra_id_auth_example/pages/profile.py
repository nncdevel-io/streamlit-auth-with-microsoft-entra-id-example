"""プロファイルページ - IDトークンからのユーザー情報を表示。"""

import streamlit as st

from entra_id_auth_example import (
    get_current_user,
    get_token_claims,
    render_sidebar_account,
    render_site_header,
    require_auth,
)

st.set_page_config(
    page_title="Profile",
    page_icon="👤",
)

# サイドバーアカウントを表示
render_sidebar_account()

# サイトヘッダー
render_site_header()

# ガード: 認証必須
require_auth()

user = get_current_user()
claims = get_token_claims()

if user is None or claims is None:
    st.stop()

st.subheader("👤 プロファイル")

st.markdown("##### 基本情報")
st.json(user)

st.markdown("##### IDトークンクレーム")
st.json(claims)
