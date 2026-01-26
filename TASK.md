# TASKS

## Task List

| ID       | Status | Summary                                             | DependsOn                           |
| -------- | ------ | --------------------------------------------------- | ----------------------------------- |
| TASK-001 | ✅     | pyproject.toml作成（依存関係定義）                  | -                                   |
| TASK-002 | ✅     | .env.example作成（Entra ID設定テンプレート）        | TASK-001                            |
| TASK-003 | ✅     | MSAL認証モジュール実装（auth.py）                   | TASK-001                            |
| TASK-004 | ✅     | コールバックハンドラ実装（認可コード交換）          | TASK-003                            |
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

## Task Details

### TASK-001

- 備考: 依存関係 - streamlit, msal, python-dotenv
- 備考: Python 3.10以上

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

- 備考: dotenv_values()で.envからのみ読み込む
- 備考: ENV=productionで環境変数から読み込む
- 備考: 設定読み込み元をログ出力

### TASK-014

- 備考: streamlit_entra_auth → entra_id_auth_example
