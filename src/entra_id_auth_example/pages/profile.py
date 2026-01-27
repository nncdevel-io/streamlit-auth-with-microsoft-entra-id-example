"""プロファイルページ - IDトークンからのユーザー情報を表示。"""

import streamlit as st

from entra_id_auth_example import get_current_user, get_token_claims, require_auth

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
