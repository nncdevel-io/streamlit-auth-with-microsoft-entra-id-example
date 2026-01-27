# アプリケーション仕様書

| 項目 | 内容 |
|------|------|
| バージョン | 0.2.0 |
| 更新日 | 2026年1月27日 |

## アプリケーション概要

本アプリケーションは、StreamlitフレームワークにMicrosoft Entra ID（旧Azure AD）認証を組み込んだサンプル実装です。OpenID Connect（OIDC）のAuthorization Code Flowを使用し、企業向けシングルサインオン（SSO）機能を提供します。

### 目的

- Streamlitアプリケーションへの企業認証の導入方法を示す
- MSAL（Microsoft Authentication Library）を使用した安全な認証フローの実装例を提供する
- 認証必須ページと公開ページの共存パターンを示す

### 技術スタック

| 項目 | 技術 |
|------|------|
| フレームワーク | Streamlit >=1.37.0 |
| マルチページ | `st.navigation()` API |
| 認証プロトコル | OpenID Connect (OIDC) |
| IdP | Microsoft Entra ID |
| 認証ライブラリ | MSAL (Microsoft Authentication Library) |
| CSRF対策 | Cookie + HMAC Double Submit |
| 言語 | Python 3.13+ |

## 機能一覧

| 機能名 | 説明 |
|--------|------|
| ログイン | Microsoft Entra IDを使用したシングルサインオン。ログインボタン押下でEntra IDのログインページにリダイレクトする。 |
| ログアウト | セッションをクリアし、Entra IDのログアウトエンドポイントにリダイレクトする。ログアウト後はアプリケーションのトップページに戻る。 |
| 認証コールバック処理 | Entra IDからの認可コードを受け取り、トークンに交換する。Cookie + HMAC Double Submit方式でstateパラメーターを検証する。 |
| ユーザー情報取得 | IDトークンのclaimsからユーザーID、名前、メールアドレスを抽出して表示する。 |
| 認証ガード | 認証が必要なページへの未認証アクセスをブロックし、ログインボタンを表示する。 |
| サイドバーアカウント表示 | 認証済み時にサイドバー下部にユーザーアバター（イニシャル）、名前、メールアドレス、ログアウトボタンを表示する。未認証時はサイドバーを非表示にする。 |
| サイトヘッダー | 全ページ共通のヘッダーを表示。左側にサイトタイトル（ホームへのリンク）、右側にAboutページへのリンク（?アイコン）を配置。 |

## 画面一覧

### アプリ構成

`st.navigation()` APIによるマルチページ構成。`app.py` がエントリポイントとして共通レイアウト（サイトヘッダー、サイドバー）を描画し、各ページは固有のコンテンツのみを担当する。

```text
app.py（エントリポイント）
├── OAuthコールバック処理（?code= 検知時）
├── 共通レイアウト（サイドバー、ヘッダー）
└── st.navigation()
    ├── Home    （/）        → pages/home.py
    ├── About   （/about）    → pages/about.py
    ├── Dashboard（/dashboard）→ pages/dashboard.py
    └── Profile （/profile）  → pages/profile.py
```

### ホーム画面（/）

**認証**: 不要（ただし認証状態で表示内容が変わる）

#### 未認証時

| 要素 | 説明 |
|------|------|
| サイトヘッダー | サイトタイトルとAboutリンクを表示 |
| メッセージ | 「このアプリケーションを使用するにはログインが必要です。」を表示 |
| ログインボタン | 「Microsoft アカウントでログイン」ボタン。押下するとEntra IDログインページにリダイレクト |

#### 認証済み時

| 要素 | 説明 |
|------|------|
| サイトヘッダー | サイトタイトルとAboutリンクを表示 |
| サイドバー | 下部にユーザーアカウント情報とログアウトボタンを表示 |
| ウェルカムメッセージ | 「ようこそ、{ユーザー名}さん！」を表示 |
| ユーザー情報 | ユーザーID、メールアドレスを表示 |
| ログアウトボタン | 押下するとログアウト処理を実行 |

### ダッシュボード画面（/dashboard）

**認証**: 必須

| 要素 | 説明 |
|------|------|
| サイトヘッダー | サイトタイトルとAboutリンクを表示 |
| サイドバー | 下部にユーザーアカウント情報とログアウトボタンを表示 |
| ページタイトル | 「{ユーザー名}のダッシュボード」を表示 |
| 説明文 | 「認証済みユーザーのみがアクセスできるページです。」を表示 |
| 統計情報 | アクティブユーザー数、セッション数、リクエスト数をメトリクスカードで表示（サンプルデータ） |

### プロファイル画面（/profile）

**認証**: 必須

| 要素 | 説明 |
|------|------|
| サイトヘッダー | サイトタイトルとAboutリンクを表示 |
| サイドバー | 下部にユーザーアカウント情報とログアウトボタンを表示 |
| ページタイトル | 「プロファイル」を表示 |
| 基本情報 | ユーザーID、名前、メールアドレスをJSON形式で表示 |
| IDトークンクレーム | IDトークンの全claimsをJSON形式で表示（sub, name, email, iss, aud, exp等） |

### About画面（/about）

**認証**: 不要

| 要素 | 説明 |
|------|------|
| サイトヘッダー | サイトタイトルとAboutリンクを表示 |
| サイドバー | 認証済み時のみ表示 |
| ページタイトル | 「About」を表示 |
| アプリ説明 | 「このアプリケーションはMicrosoft Entra ID認証のサンプル実装です。」を表示 |
| 機能一覧 | SSO、ユーザー情報取得、セッション管理、認証ガード機能の説明 |
| 技術スタック | Streamlit、OIDC、Entra ID、MSALの説明 |

## その他

### 認証フロー

```text
1. ユーザーがログインボタンをクリック
2. アプリがCSRF対策用のnonceを生成
3. nonceをブラウザCookieに保存（components.html経由でJavaScript実行）
4. HMAC署名付きstate（nonce.HMAC(nonce, secret)）を生成
5. Entra IDの認可エンドポイントにstateを付与してリダイレクト
6. ユーザーがEntra IDでログイン
7. Entra IDがアプリのリダイレクトURL（/callback）に認可コードとstateを付与してリダイレクト
8. app.pyがクエリパラメーター（?code=）を検知
9. Cookieからnonceを取得し、stateのHMAC署名 + nonce一致を検証（CSRF対策）
10. アプリが認可コードをトークンエンドポイントでIDトークンに交換
11. MSALがIDトークンを自動検証（署名、iss、aud、exp等）
12. IDトークンのclaimsからユーザー情報を抽出してセッションに保存
13. st.rerun()でページを再描画し、認証済み状態を表示
```

### CSRF対策: Cookie + HMAC Double Submit方式

Streamlitでは外部IdPへのリダイレクト（ブラウザのフルページナビゲーション）を挟むと`st.session_state`が失われる（セッションIDが変わるため）。そのため、OAuth stateパラメーターの検証にはブラウザCookieを使用する。

| 項目 | 説明 |
|------|------|
| nonce生成 | `secrets.token_urlsafe(32)` |
| 署名 | `HMAC-SHA256(nonce, client_secret)` |
| stateパラメーター | `nonce.signature` |
| Cookie保存 | `components.html()` 経由でJavaScript実行 |
| Cookie読み取り | `st.context.cookies`（Streamlit 1.37+） |
| 検証 | 署名再計算 + `hmac.compare_digest` による一致確認 |

### セッション管理

- Streamlitの`st.session_state`を使用（認証情報の保持）
- 保存するデータ:
  - `authenticated`: 認証状態（bool）
  - `user`: ユーザー情報（id, name, email）
  - `token_claims`: IDトークンの全claims

### 環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| AZURE_CLIENT_ID | アプリケーション（クライアント）ID | Yes |
| AZURE_CLIENT_SECRET | クライアントシークレット | Yes |
| AZURE_TENANT_ID | ディレクトリ（テナント）ID | Yes |
| AZURE_REDIRECT_URI | リダイレクトURI | No（デフォルト: `http://localhost:8501/callback`） |
| SSL_CA_FILE | カスタムCA証明書ファイル | No |
| ENV | 環境識別子（`production`で環境変数から読み込み、それ以外は.envから読み込み） | No |

### セキュリティ考慮事項

- CSRF対策: Cookie + HMAC Double Submit方式によるstateパラメーター検証
- IDトークン検証: MSALによる自動検証（署名、発行者、対象者、有効期限）
- 環境変数分離: 開発環境は.envファイルのみ、本番環境は環境変数のみから設定を読み込み
- クライアントシークレット: サーバーサイドで安全に管理（ConfidentialClientApplication使用）
- Cookie属性: SameSite=Lax、HTTPS環境ではSecureフラグ付加、10分のTTL
