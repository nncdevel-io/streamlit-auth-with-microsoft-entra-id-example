# TASKS

## Task List

| ID       | Status | Summary                                             | DependsOn                           |
| -------- | ------ | --------------------------------------------------- | ----------------------------------- |
| TASK-001 | ✅     | pyproject.toml作成（依存関係定義）                  | -                                   |
| TASK-002 | ✅     | .env.example作成（Entra ID設定テンプレート）        | TASK-001                            |
| TASK-003 | ✅     | MSAL認証モジュール実装（client.py）                 | TASK-001                            |
| TASK-004 | ✅     | コールバックハンドラー実装（認可コード交換）        | TASK-003                            |
| TASK-005 | ✅     | IDトークン検証ロジック実装                          | TASK-003                            |
| TASK-006 | ✅     | ログアウト機能実装（Entra IDリダイレクト）          | TASK-003                            |
| TASK-007 | ✅     | セッション管理ユーティリティ実装                    | TASK-003                            |
| TASK-008 | ✅     | メインStreamlitアプリ作成（app.py）                 | TASK-004,TASK-005,TASK-006,TASK-007 |
| TASK-009 | ✅     | 認証モジュールのユニットテスト作成                  | TASK-003,TASK-004,TASK-005          |
| TASK-010 | ✅     | Makefile作成                                        | -                                   |
| TASK-011 | ✅     | devcontainer環境作成                                | -                                   |
| TASK-012 | ✅     | linter設定ファイル作成（cspell, markdownlint等）    | -                                   |
| TASK-013 | ✅     | 環境変数読み込み分離（開発:.env/本番:環境変数）     | TASK-003                            |
| TASK-014 | ✅     | パッケージ名変更（entra_id_auth_example）           | -                                   |
| TASK-015 | ✅     | README更新                                          | TASK-014                            |
| TASK-016 | ✅     | CSRF対策をCookie+HMAC Double Submit方式に変更       | TASK-004                            |
| TASK-017 | ✅     | st.navigation() APIへの移行                         | TASK-008,TASK-016                   |
| TASK-018 | ✅     | ドキュメント最新化                                  | TASK-016,TASK-017                   |

## Task Details

### TASK-001

- 備考: 依存関係 - streamlit, msal, python-dotenv
- 備考: Python 3.13以上

### TASK-002

- 備考: 必要なキー - AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID
- 注意: 実際のシークレットはコミットしないこと

### TASK-003

- 備考: MSAL ConfidentialClientApplicationを使用
- 備考: Authorization Code Flowの実装

### TASK-004

- 備考: 認可コードをIDトークン・アクセストークンに交換
- 注意: トークンエンドポイントのエラーハンドリング

### TASK-005

- 備考: 署名、発行者（issuer）、対象者（audience）、有効期限を検証
- 注意: MSALの組み込み検証機能を可能な限り使用

### TASK-007

- 備考: ユーザー情報（sub, name, preferred_username, email）をst.session_stateに格納
- 備考: is_authenticated()ユーティリティ関数を提供

### TASK-008

- 備考: リダイレクトURI: `http://localhost:8501/callback`（開発時）
- 備考: 未認証ユーザーにはログインボタンを表示

### TASK-010

- 備考: install, run, test, lint, type-check, check, cleanコマンド

### TASK-011

- 備考: Python 3.13、uv、VS Code拡張機能

### TASK-012

- 備考: cspell.json, .markdownlint-cli2.jsonc, .textlintrc.json

### TASK-013

- 備考: dotenv_values()で`.env`からのみ読み込む
- 備考: ENV=productionで環境変数から読み込む
- 備考: 設定読み込み元をログ出力

### TASK-014

- 備考: streamlit_entra_auth → entra_id_auth_example

### TASK-016

- 課題: 外部IdPリダイレクト時にst.session_stateが失われる（セッションIDが変わるため）
- 対策: OAuth stateの検証にsession_stateではなくブラウザCookieを使用
- 方式: Cookie + HMAC Double Submit
  - ログイン時にnonceを生成し、Cookieに保存
  - HMAC-SHA256(nonce, client_secret)で署名し、stateパラメーターとして使用
  - コールバック時にst.context.cookiesでnonceを取得し、HMAC検証
- Cookie設定: components.html()（sandboxed iframe、allow-same-origin）でJavaScript実行
- リダイレクト: st.markdown() meta refreshで実行（iframeはallow-top-navigationなし）
- テスト: _create_signed_state,_verify_stateのユニットテスト追加

### TASK-017

- 課題: ファイルベースマルチページでは pages/ 内の全ファイルがサイドバーに表示される
- 対策: st.navigation() APIに移行し、表示ページを明示的に制御
- 変更点:
  - app.py: エントリポイント/ルーターに変更（共通レイアウト + st.navigation）
  - pages/home.py: 新規作成（旧app.pyのメインコンテンツを移動）
  - pages/callback.py: 削除（OAuthコールバックはapp.pyで直接処理）
  - 各ページ: st.set_page_config(), render_sidebar_account(), render_site_header()を削除
  - pyproject.toml: streamlit>=1.37.0に更新
- redirect_uri: /callback（Entra IDからのリダイレクト先。app.pyで```?code=```を検知して処理）

### TASK-018

- 更新対象: README.md, CLAUDE.md, ARCHITECTURE.md, REQUIREMENTS.md, SPECIFICATION.md, TASK.md
- 主な更新内容:
  - CSRF対策方式の記載追加（Cookie + HMAC Double Submit）
  - st.navigation() APIへの移行に伴うアーキテクチャ記載の更新
  - ディレクトリ構成の最新化（pages/home.py追加、callback.py削除）
  - redirect_uri、公開API一覧、セッション管理の説明を更新
