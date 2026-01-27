"""Aboutページ - 認証なしでアクセス可能。"""

import streamlit as st

st.subheader("ℹ️ About")

st.write("このアプリケーションはMicrosoft Entra ID認証のサンプル実装です。")

st.markdown("##### 機能")
st.markdown("""
- Microsoft Entra IDによるシングルサインオン（SSO）
- IDトークンからのユーザー情報取得
- セッション管理
- 認証必須ページのガード機能
""")

st.markdown("##### 技術スタック")
st.markdown("""
- **フレームワーク**: Streamlit
- **認証**: OpenID Connect (OIDC)
- **IdP**: Microsoft Entra ID
- **ライブラリ**: MSAL (Microsoft Authentication Library)
""")
