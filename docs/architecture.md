# Streamlit Entra ID Authentication - アーキテクチャ設計書

| 項目 | 内容 |
| ------ | ------ |
| バージョン | 0.2.0 |
| 作成日 | 2026年1月24日 |
| 更新日 | 2026年1月27日 |

---

## 1. システム構成

### 1.1 認証フロー

```text
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Browser   │      │  Streamlit  │      │  Entra ID   │
│             │      │    App      │      │             │
└──────┬──────┘      └──────┬──────┘      └──────┬──────┘
       │                    │                    │
       │  1. アクセス       │                    │
       │───────────────────>│                    │
       │                    │                    │
       │  2. 未認証→ログインボタン表示           │
       │<───────────────────│                    │
       │                    │                    │
       │  3. ログインボタン押下                  │
       │───────────────────>│                    │
       │                    │                    │
       │  4. Cookie設定（nonce）+ リダイレクト   │
       │<───────────────────│                    │
       │                    │                    │
       │  5. 認証リクエスト（state=nonce.HMAC）  │
       │────────────────────────────────────────>│
       │                    │                    │
       │  6. ログイン画面                        │
       │<────────────────────────────────────────│
       │                    │                    │
       │  7. 認証情報入力                        │
       │────────────────────────────────────────>│
       │                    │                    │
       │  8. 認可コード＋state付きリダイレクト   │
       │<────────────────────────────────────────│
       │                    │                    │
       │  9. コールバック（?code=&state=）        │
       │───────────────────>│                    │
       │                    │                    │
       │                    │ 10. Cookie nonce +  │
       │                    │     state HMAC検証  │
       │                    │                    │
       │                    │ 11. トークン交換    │
       │                    │───────────────────>│
       │                    │                    │
       │                    │ 12. ID Token       │
       │                    │<───────────────────│
       │                    │                    │
       │ 13. 認証完了       │                    │
       │<───────────────────│                    │
       │                    │                    │
```

### 1.2 技術スタック

| コンポーネント | 技術 |
| --------------- | ------ |
| フレームワーク | Streamlit >=1.37.0 |
| マルチページ | `st.navigation()` API |
| 認証プロトコル | OpenID Connect (OIDC) |
| IdP | Microsoft Entra ID |
| OIDCライブラリ | `msal` (Microsoft Authentication Library) |
| CSRF対策 | Cookie + HMAC Double Submit |
| セッション管理 | `st.session_state`（認証情報の保持） |

### 1.3 CSRF対策: Cookie + HMAC Double Submit方式

OAuth認証フローのCSRF対策として、Cookie + HMAC Double Submit方式を採用する。

**背景**: Streamlitでは外部IdPへのリダイレクト（ブラウザのフルページナビゲーション）を挟むと
`st.session_state` が失われる（セッションIDが変わるため）。そのため、stateパラメーターの検証に
session_stateではなくブラウザCookieを使用する。

**フロー:**

1. ログイン時: ランダムなnonceを生成し、`HMAC-SHA256(nonce, client_secret)` で署名
2. nonceをブラウザCookieに保存（`components.html()` でJavaScript実行）
3. `nonce.signature` をOAuthのstateパラメーターとして使用
4. コールバック時: `st.context.cookies` でCookieからnonceを取得
5. stateのHMAC署名を再計算し、署名一致 + nonce一致を検証

---

## 2. ディレクトリ構成

```text
streamlit-entra-auth/
├── src/
│   └── entra_id_auth_example/
│       ├── __init__.py        # 公開関数のエクスポート
│       ├── config.py          # 設定管理
│       ├── client.py          # MSALクライアント
│       ├── handlers.py        # 認証ハンドラ・UIコンポーネント
│       ├── app.py             # エントリポイント（ルーター + 共通レイアウト）
│       └── pages/
│           ├── __init__.py
│           ├── home.py        # ホームページ
│           ├── about.py       # Aboutページ（認証不要）
│           ├── dashboard.py   # 認証必須ページ例
│           └── profile.py     # プロファイルページ例
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_client.py
│   └── test_handlers.py
├── docs/
│   ├── REQUIREMENTS.md        # 要件定義書
│   ├── ARCHITECTURE.md        # 本ドキュメント
│   └── SPECIFICATION.md       # アプリケーション仕様書
├── .env.example               # 環境変数テンプレート
├── .streamlit/
│   └── config.toml            # Streamlit設定
├── .python-version            # Pythonバージョン指定（uv/pyenv用）
├── pyproject.toml             # プロジェクト設定
├── uv.lock                    # 依存関係ロックファイル
├── Makefile
├── README.md
└── LICENSE
```

### 2.1 src layoutを採用する理由

- ローカルソースの誤importを防止
- `pip install -e .` によるeditable installを強制
- テスト時にインストール済みパッケージをテストすることを保証
- PyPA、pytest等の推奨構成に準拠

---

## 3. インターフェイズ仕様

### 3.1 設定

環境変数または`.env`ファイルで設定を管理する。

| 環境変数 | 説明 | 例 |
| --------- | ------ | ----- |
| `AZURE_CLIENT_ID` | アプリケーション（クライアント）ID | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `AZURE_CLIENT_SECRET` | クライアントシークレット | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `AZURE_TENANT_ID` | ディレクトリ（テナント）ID | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `AZURE_REDIRECT_URI` | リダイレクトURI（デフォルト: `http://localhost:8501/`） | `http://localhost:8501/` |
| `SSL_CA_FILE` | カスタムCA証明書ファイル（任意） | `/path/to/ca.pem` |
| `ENV` | 環境識別子（`production`で環境変数から読み込み） | `production` |

### 3.2 公開関数

#### login()

Entra IDのログインページにリダイレクトする。

```python
def login() -> None:
    """認証フローを開始し、Entra IDにリダイレクト"""
```

#### logout()

セッションをクリアし、Entra IDからログアウトする。

```python
def logout() -> None:
    """セッションをクリアし、Entra IDのログアウトエンドポイントにリダイレクト"""
```

#### handle_callback()

認可コードを処理し、トークンを取得する。

```python
def handle_callback() -> bool:
    """
    コールバックURLのクエリパラメータを処理

    Returns:
        bool: 認証成功時True
    """
```

#### is_authenticated()

現在の認証状態を確認する。

```python
def is_authenticated() -> bool:
    """認証済みかどうかを返す"""
```

#### get_current_user()

現在のユーザー情報を取得する。

```python
def get_current_user() -> UserInfo | None:
    """
    認証済みユーザーの情報を返す

    Returns:
        UserInfo: {"id": str, "name": str, "email": str}
        None: 未認証の場合
    """
```

#### get_token_claims()

生のIDトークンclaimsを取得する。

```python
def get_token_claims() -> dict[str, Any] | None:
    """
    MSALによる検証済みIDトークンのclaimsを返す

    Returns:
        dict: sub, name, email, iss, aud, exp等を含むclaims
        None: 未認証の場合
    """
```

#### require_auth()

認証を必須とするページガード関数。

```python
def require_auth() -> None:
    """
    未認証の場合、エラーメッセージとログインボタンを表示してst.stop()
    """
```

#### render_site_header()

全ページ共通のサイトヘッダーを表示する。

```python
def render_site_header() -> None:
    """固定ヘッダーバー（タイトル + Aboutリンク）を表示"""
```

#### render_sidebar_account()

サイドバーにユーザーアカウント情報を表示する。

```python
def render_sidebar_account() -> None:
    """
    認証済み: サイドバー下部にアバター・名前・ログアウトボタンを表示
    未認証: サイドバーを非表示
    """
```

### 3.3 セッションデータ構造

認証成功時、以下のデータを`st.session_state`に格納する。

```python
st.session_state["authenticated"] = True
st.session_state["user"] = {
    "id": "...",
    "name": "...",
    "email": "...",
}
st.session_state["token_claims"] = {...}  # 生のクレーム
```

CSRF対策用のstateは`st.session_state`ではなくブラウザCookieで管理する
（外部IdPへのリダイレクトでセッションが失われるため）。

---

## 4. モジュール設計

### 4.1 config.py

環境変数の読み込みと設定管理を担当。

```python
@dataclass(frozen=True)
class AuthConfig:
    client_id: str
    client_secret: str
    tenant_id: str
    redirect_uri: str
    ssl_ca_file: str | None = None

    @property
    def authority(self) -> str: ...
    @property
    def base_url(self) -> str: ...
    @property
    def logout_url(self) -> str: ...
```

### 4.2 client.py

MSALクライアントのラッパー。

```python
class EntraAuthClient:
    def __init__(self, config: AuthConfig): ...
    def get_auth_url(self, state: str) -> str: ...
    def acquire_token_by_code(self, code: str) -> dict: ...

    @property
    def logout_url(self) -> str: ...
```

### 4.3 handlers.py

Streamlit統合の認証ハンドラーとUIコンポーネント。

```python
# 認証フロー
def login() -> None: ...
def logout() -> None: ...
def handle_callback() -> bool: ...

# 認証状態
def is_authenticated() -> bool: ...
def get_current_user() -> UserInfo | None: ...
def get_token_claims() -> dict[str, Any] | None: ...
def require_auth() -> None: ...

# UIコンポーネント
def render_site_header() -> None: ...
def render_sidebar_account() -> None: ...

# 内部: CSRF対策
def _create_signed_state(secret: str) -> tuple[str, str]: ...
def _verify_state(state: str | None, cookie_nonce: str | None, secret: str) -> bool: ...
```

### 4.4 app.py（エントリポイント）

`st.navigation()` APIを使用したルーター兼共通レイアウト。

```python
# 1. OAuthコールバック処理（st.navigation前に実行）
if "code" in st.query_params:
    handle_callback()

# 2. 共通レイアウト
render_sidebar_account()
render_site_header()

# 3. ページ定義・ルーティング
pg = st.navigation([...])
pg.run()
```

### 4.5 **init**.py

公開APIのエクスポート。

```python
__all__ = [
    "AuthConfig",
    "EntraAuthClient",
    "get_current_user",
    "get_token_claims",
    "handle_callback",
    "is_authenticated",
    "load_config",
    "login",
    "logout",
    "render_sidebar_account",
    "render_site_header",
    "require_auth",
]
```
