"""Streamlitサーバーの起動設定。

`streamlit run` にこのファイルを指定すると、Streamlitは `app` のst.Appを検出して起動する。
.envまたは環境変数から読み込んだ認証設定を、st.login()が参照するsecretsとして渡す。
"""

from pathlib import Path

import streamlit as st

from entra_id_auth_example.callback import create_callback_routes
from entra_id_auth_example.config import load_config

_config = load_config()

app = st.App(
    Path(__file__).with_name("app.py"),
    secrets=_config.to_streamlit_secrets(),
    routes=create_callback_routes(_config.redirect_uri),
)
