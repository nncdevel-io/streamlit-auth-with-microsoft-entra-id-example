"""ホームページ。"""

import streamlit as st

from entra_id_auth_example import get_current_user, is_authenticated, login, logout

if is_authenticated():
    user = get_current_user()
    if user is None:
        st.stop()

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
else:
    st.info("このアプリケーションを使用するにはログインが必要です。")

    if st.button("Microsoft アカウントでログイン", type="primary"):
        login()
