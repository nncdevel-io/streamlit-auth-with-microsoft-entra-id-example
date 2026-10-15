# 依存関係の更新による影響一覧

`uv lock --upgrade` で上がる依存のうち、このアプリのコードに影響する変更をまとめる（2026-10-15 時点、Python 3.13）。
確認には、更新後の依存を入れた一時環境での実行結果と、各パッケージの公式の更新履歴を使った。

## 主な更新

| パッケージ | 更新前 | 更新後 |
| --- | --- | --- |
| streamlit | 1.54.0 | 1.66.0 |
| msal | 1.34.0 | 1.39.0 |
| mypy | 1.19.1 | 2.4.0 |
| ruff | 0.14.14 | 0.17.0 |
| requests | 2.33.0 | 2.34.2 |
| pandas | 2.3.3 | 3.0.6 |
| protobuf | 6.33.5 | 7.36.2 |
| cryptography | 48.0.1 | 50.0.2 |

streamlit 1.66.0 では、サーバーが tornado から starlette と uvicorn に置き換わる。
pandas 3 と protobuf 7 は streamlit 1.54.0 の依存範囲外なので、streamlit と一緒に上げる必要がある。

## 対応が必要な変更

| 変更 | 影響する箇所 | 対応案 | 出典 |
| --- | --- | --- | --- |
| msal 1.38.0 で ID トークンの検証をやめ、`decode_id_token` を非推奨にした | `client.py:108-119`、`handlers.py` の ID トークンのクレームを使う処理、`docs/requirements.md` の REQ-3、`docs/specification.md:133` | 要件 REQ-3（署名・発行者・対象者・有効期限の検証）を満たさなくなる。アプリ側で検証を実装するか、要件を見直すかの判断が要る | [msal 1.38.0](https://github.com/AzureAD/microsoft-authentication-library-for-python/releases/tag/1.38.0)（PR #943） |
| requests 2.34.0 が型情報を同梱し、`init_poolmanager` に型が付いた | `client.py:44` | 不要になった `# type: ignore[no-untyped-call]` を削除する（mypy の strict モードで unused-ignore エラーになる）。types-requests は外せる見込み | [requests HISTORY.md](https://github.com/psf/requests/blob/main/HISTORY.md) |
| streamlit で `st.button` の `use_container_width` が非推奨になった | `handlers.py:465` | `width="stretch"` に置き換える | streamlit 1.66.0 の `elements/widgets/button.py` の docstring |

## 影響がないことを確認した項目

| 項目 | 確認方法と結果 |
| --- | --- |
| `streamlit.runtime.scriptrunner.get_script_run_ctx`（非公開 API） | 1.66.0 で import できる |
| `components.html` の iframe での Cookie 設定 | 1.66.0 でも iframe に `allow-same-origin` と `allow-scripts` が付き、設定した Cookie がページから見える |
| `st.markdown` に書いた `<meta http-equiv="refresh">` によるリダイレクト | 1.66.0 で実行される |
| `st.context.cookies` による Cookie の読み取り | 1.66.0 で JS から設定した Cookie を読める |
| `/callback` パスでのアプリ本体の表示と `st.query_params` | 1.66.0 で200を返し、クエリパラメーターを読める |
| `.stMainBlockContainer`、`[data-testid="stSidebar"]` | 1.66.0 の画面のコードに残っている |
| `.streamlit/config.toml` の `client.toolbarMode` | 1.66.0 の設定項目に残っている |
| ruff 0.17.0 | `ruff check` と `ruff format --check` で指摘なし |
| mypy 2.4.0 | `client.py:44` の1件以外にエラーなし |
| pytest 9.1.1 | 35件成功 |
| msal の `http_client`、`get_authorization_request_url`、`acquire_token_by_authorization_code` | 1.39.0 でも引数が変わっていない |

## 更新とは関係なく見つかった問題

- msal 1.34.0 でも、ID トークンの署名は検証していない
  - `msal/oauth2cli/oidc.py` の `decode_id_token` は、ペイロードを復号して iss・aud・nonce・有効期限を確かめるだけ
  - `client.py:108-109` と `docs/specification.md:133` の「署名検証（JWKS）」という記述は、更新前から実装と合っていない
- `[data-testid="stSidebarCollapsedControl"]` は、1.54.0 の画面のコードにもない。このセレクターは更新前から効いていない
- `api-docs/` は git の管理外で `conf.py` がないため、`make docs` は更新前から動かない見込み（未確認）

## 未確認の項目

- 実際の Entra ID でのログインからログアウトまでの流れ（Microsoft への通信を伴うため実施していない）
- urllib3 2.8.0 で、HTTPS の転送プロキシーを使う場合の `ssl_context` の扱いが変わった。社内プロキシーが `https://` 指定の場合に `SSL_CA_FILE` が効くかは確認していない
- 表示が崩れていないか（画面での確認）
- pytest、pytest-cov、sphinx-autodoc-typehints の更新履歴は読んでいない（実行結果に問題はない）
