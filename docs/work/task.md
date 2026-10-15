---
title: Python 3.13 以上を維持した依存関係の最新版へのバージョンアップ
priority: medium
created: 2026-10-15
owner: t-izuno
related:
  - docs/task.md
  - docs/requirements.md
  - docs/specification.md
---

<!-- markdownlint-disable-next-line MD025 -->
# TASKS

マイルストーン: 依存関係のバージョンアップ
ゴール: Python 3.13 以上の対応を保ったまま全依存関係を最新版に上げ、更新前と同じ認証フローが動くことを確認する

## ワークフロールール

- タスク着手時にステータスを 🚧 に更新する
- 必要な検証をエージェント単独で完遂できた場合は ✅、人の確認が残る場合は 🧪 に更新し、未確認事項を明記する。判断がつかない場合は 🧪 に倒す
- 🧪 から ✅ への更新はユーザーのレビュー承認をもって行う
- DependsOn のタスクがすべて ✅ でないタスクには着手しない

## ステータス表記ルール

| Status | 意味 |
| --- | --- |
| ⏳ | 未着手、TODO |
| 🚧 | 作業中、IN_PROGRESS |
| 🧪 | 確認待ち、REVIEW |
| ✅ | 完了、DONE |
| 🚫 | 中止、CANCELLED |

## タスク一覧

| ID | Status | Summary | DependsOn |
| --- | --- | --- | --- |
| TASK-001 | ✅ | 開発用依存を dependency-groups へ移し make install-dev で導入できるようにする | - |
| TASK-002 | ✅ | requests を直接依存として pyproject.toml に追加する | - |
| TASK-003 | ✅ | handlers.py に残っている ruff format の差分を解消する | - |
| TASK-004 | ✅ | GitHub Actions で make test と make check を実行する CI を作る | TASK-001,TASK-002,TASK-003 |
| TASK-005 | ✅ | .venv を作り直し、更新前のテスト・lint・型チェック・起動の結果を記録する | TASK-004 |
| TASK-006 | 🚫 | 更新前の状態で Entra ID のログインからログアウトまでを確認し記録する | TASK-005 |
| TASK-007 | ✅ | 各依存の更新履歴を読み、コードに影響する変更の一覧を作る | - |
| TASK-008 | ✅ | pyproject.toml の下限を最新版に上げ、uv.lock を全依存の最新版で作り直す | TASK-005 |
| TASK-009 | ✅ | ruff の新しいバージョンで出る lint と format の指摘を解消する | TASK-008 |
| TASK-010 | ✅ | mypy 2.x の strict モードで出る型エラーを解消する | TASK-008 |
| TASK-011 | ✅ | 影響一覧に沿ってコードとテストを直し、make test を通す | TASK-007,TASK-008 |
| TASK-017 | 🧪 | PyJWT で ID トークンの署名・発行者・対象者・有効期限・nonce を検証する処理を実装する | TASK-008 |
| TASK-012 | 🧪 | make docs で API ドキュメントを生成できることを確認する | TASK-008 |
| TASK-013 | 🧪 | ヘッダーとサイドバーのカスタム CSS を Streamlit 最新版の画面に合わせて直す | TASK-011 |
| TASK-014 | ⏳ | 更新後に Entra ID のログインからログアウトまでを確認し、更新前と比べる | TASK-011,TASK-013,TASK-017 |
| TASK-015 | ⏳ | SSL_CA_FILE を指定した社内プロキシー環境で Entra ID に接続できることを確認する | TASK-011 |
| TASK-016 | ✅ | README と docs の Streamlit のバージョン記載を更新する | TASK-008 |

## タスク詳細（補足が必要な場合のみ）

### TASK-001

- 補足: `[project.optional-dependencies]` の `dev` は `uv sync --dev` では導入されず、`make install-dev` 後も pytest が入らない

### TASK-004

- 補足: Python 3.13 で実行する
- 補足: プッシュとプルリクエストを契機に実行する
- 補足: GitHub 上で成功（コミット 4ff76e9、[実行結果](https://github.com/nncdevel-io/streamlit-auth-with-microsoft-entra-id-example/actions/runs/38672062125)）

### TASK-005

- 補足: 記録する項目は Python・streamlit・msal の版、`make test`、`make check`、`ruff format --check`、`streamlit run` での起動結果、CI の結果
- 補足: 記録（2026-10-15）: Python 3.13.9、streamlit 1.54.0、msal 1.34.0
- 補足: 記録（2026-10-15）: `make test` は35件成功、`make check` と `ruff format --check` は指摘なし
- 補足: 記録（2026-10-15）: `streamlit run` で `/_stcore/health` が `ok`、トップページが200（`.env` なしのため認証処理は通していない）
- 補足: 記録（2026-10-15）: CI は Python 3.13.16 で成功。テスト35件成功、ruff と mypy は指摘なし

### TASK-006

- 補足: 中止。更新前の動作は過去に確認済みのため、その結果を比較の基準とする
- 補足: 実際の Entra ID のアプリ登録と `.env` が要るため、利用者が実施する
- 補足: 確認項目は、ログイン、コールバック、CSRF の Cookie 検証、ログアウト、各ページの表示、不正な `state` の拒否、`ENV=production` での設定読み込み

### TASK-007

- 補足: 成果物は `docs/work/dependency-impact.md`
- 補足: msal 1.38.0 で ID トークンの検証がなくなった件は、アプリ側で検証を実装する方針に決定（TASK-017）
- 補足: 対象は streamlit 1.55〜1.66、msal 1.35〜1.39、mypy 2.x、pandas 3.x、protobuf 7.x、cryptography 47〜50
- 注意: `streamlit.runtime.scriptrunner.get_script_run_ctx`（非公開 API）と `components.html` の変更を必ず確認する
- 注意: `st.context.cookies` と `st.query_params` の変更も必ず確認する

### TASK-008

- 補足: メジャー更新も含めて、すべての依存を最新版にする
- 注意: `requires-python = ">=3.13"`、`.python-version`、devcontainer のイメージは変えない
- 注意: Python 3.13 に対応していない版は採用しない

### TASK-013

- 注意: 表示が崩れていないかは利用者が画面で判断する
- 補足: 1.66.0 の画面で、ヘッダーと未ログイン時の表示（サイドバー非表示）が崩れていないことを確認した。効いていなかった `stSidebarCollapsedControl` のセレクターは削除した
- 注意: 未確認事項は、ログイン後のサイドバー（アカウント情報の下部配置）の表示

### TASK-015

- 補足: 社内プロキシーの CA 証明書が要るため、利用者が実施する

### TASK-017

- 補足: msal 1.38.0 で ID トークンの検証がなくなったため、要件 REQ-3 をアプリ側で満たす
- 補足: `client.py` の docstring と `docs/specification.md` の検証の記述も実装に合わせて直す
- 注意: 認証まわりの変更のため、利用者のレビューを受ける
- 補足: 単体テストで、署名・iss・aud・exp・nbf・nonce の不一致、nonce の欠落、署名なしトークン、メタデータ取得失敗を拒否することを確認した
- 注意: 未確認事項は、利用者のレビューと、実際の Entra ID が発行したトークンでの検証（TASK-014 で確認）

### TASK-012

- 補足: `api-docs/conf.py` はコミット db34166 で削除済みのため、`make docs` は更新前から失敗する
- 補足: 削除前の `conf.py` を一時ディレクトリに取り出し、更新後の sphinx で HTML を生成できることを確認した
- 注意: 未確認事項は、`make docs` を直すか削除するかの判断（利用者の判断待ち）
