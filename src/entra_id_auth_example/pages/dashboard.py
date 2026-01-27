"""ダッシュボードページ - 認証が必要。"""

import streamlit as st

from entra_id_auth_example import get_current_user, require_auth

# ガード: 認証必須
require_auth()

user = get_current_user()
if user is None:
    st.stop()

st.subheader(f"📊 {user['name']}のダッシュボード")

st.write("認証済みユーザーのみがアクセスできるページです。")

with st.container():
    st.markdown("##### 統計情報")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("アクティブユーザー", "1,234")
    with col2:
        st.metric("セッション数", "5,678")
    with col3:
        st.metric("リクエスト", "12,345")
