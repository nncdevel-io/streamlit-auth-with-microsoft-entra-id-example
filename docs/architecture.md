# Streamlit Entra ID Authentication - アーキテクチャ設計書

| 項目 | 内容 |
| ------ | ------ |
| バージョン | 0.3.0 |
| 作成日 | 2026年1月24日 |
| 更新日 | 2026年10月20日 |

---

## 1. システム構成

### 1.1 認証フロー

```text
┌─────────────┐   ┌─────────────┐   ┌──────────────────┐   ┌─────────────┐
│   Browser   │   │  Streamlit  │   │ Streamlit Server │   │  Entra ID   │
│             │   │    App      │   │   (st.login)     │   │             │
└──────┬──────┘   └──────┬──────┘   └────────┬─────────┘   └──────┬──────┘
       │ 1. ログインボタン押下                │                    │
       │────────────────>│                   │                    │
       │                 │ 2. st.login()     │                    │
       │                 │──────────────────>│                    │
       │ 3. 認証リクエスト（state、nonce）     │                    │
       │<─────────────────────────────────────│                    │
       │──────────────────────────────────────────────────────────>│
       │ 4. ログイン画面・認証情報入力                              │
       │<─────────────────────────────────────────────────────────>│
       │ 5. /callback?code=&state= へリダイレクト                   │
       │<──────────────────────────────────────────────────────────│
       │ 6. /callback → /oauth2callback へ転送                      │
       │─────────────────────────────────────>│                    │
       │                 │                   │ 7. state検証        │
       │                 │                   │ 8. トークン交換     │
       │                 │                   │───────────────────>│
       │                 │                   │ 9. ID Token        │
       │                 │                   │<───────────────────│
       │                 │                   │ 10. ID Token検証    │
       │ 11. HttpOnly Cookie設定 + トップへリダイレクト              │
       │<─────────────────────────────────────│                    │
       │ 12. st.user で認証済み表示           │                    │
       │<────────────────│                   │                    │
```

### 1.2 技術スタック

| コンポーネント | 技術 |
| --------------- | ------ |
| フレームワーク | Streamlit >=1.66.0 |
| サーバー起動 | `st.App`（認証設定のsecrets、転送ルート） |
| マルチページ | `st.navigation()` API |
| 認証プロトコル | OpenID Connect (OIDC) |
| IdP | Microsoft Entra ID |
| OIDCライブラリ | `st.login()`（Authlib） |
| 認証情報の保持 | 署名付きのHttpOnly Cookie（`st.user`で参照） |

### 1.3 認証方式: st.login()

Streamlit組み込みの`st.login()`を使用する。stateとnonceの生成・検証、トークン交換、
IDトークンの検証、認証Cookieの発行はStreamlitサーバー（Authlib）が行う。

**設定の受け渡し**: `st.login()`は`st.secrets["auth"]`を読む。本アプリは`.env`または環境変数から
読み込んだ設定を、`server.py`で`st.App(secrets=...)`に渡す。

**コールバックのパス**: `st.login()`のコールバックは`/oauth2callback`に固定されている。
Entra IDのアプリ登録で`/callback`を使い続けるため、`/callback`で受けたリクエストを
クエリパラメーターごと`/oauth2callback`へ転送するルートを`st.App`に追加する。
トークン交換で送るredirect_uriはログイン開始時の`/callback`のままなので、アプリ登録の変更は不要である。

**プロキシー環境**: `SSL_CA_FILE`は、AuthlibがEntra IDとの通信に使うhttpxへ`verify`として渡す。

---

## 2. ディレクトリ構成

```text
streamlit-entra-auth/
├── src/
│   └── entra_id_auth_example/
│       ├── __init__.py        # 公開関数のエクスポート
│       ├── config.py          # 設定管理
│       ├── server.py          # サーバー起動設定（st.App）
│       ├── callback.py        # /callback の転送ルート
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
│   ├── test_callback.py
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
| `AZURE_REDIRECT_URI` | リダイレクトURI（デフォルト: `http://localhost:8501/callback`） | `http://localhost:8501/callback` |
| `AUTH_COOKIE_SECRET` | 認証Cookieの署名に使うシークレット | ランダムな文字列 |
| `SSL_CA_FILE` | カスタムCA証明書ファイル（任意） | `/path/to/ca.pem` |
| `ENV` | 環境識別子（`production`で環境変数から読み込み） | `production` |

### 3.2 公開関数

#### login()

Entra IDのログインページにリダイレクトする。

```python
def login() -> None:
    """st.login()で認証フローを開始し、Entra IDにリダイレクト"""
```

#### logout()

st.logout()で認証Cookieを削除し、Entra IDからログアウトする。

```python
def logout() -> None:
    """認証Cookieを削除し、Entra IDのログアウトエンドポイントにリダイレクト"""
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
    st.login()が検証して保存したIDトークンのclaims（st.user）を返す

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

### 3.3 認証情報の保持

認証成功時、`st.login()`がIDトークンのclaimsを署名付きのHttpOnly Cookieに保存する。
アプリは`st.user`で参照する。

```python
st.user.is_logged_in  # 認証状態
st.user.to_dict()     # IDトークンのclaims（sub、name、email、iss、aud、exp等）
```

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
    cookie_secret: str
    ssl_ca_file: str | None = None

    @property
    def authority(self) -> str: ...
    @property
    def server_metadata_url(self) -> str: ...
    def to_streamlit_secrets(self) -> dict[str, Any]: ...
```

### 4.2 server.py

`streamlit run`で起動するファイル。`st.App`に認証設定のsecretsと転送ルートを渡す。

```python
_config = load_config()

app = st.App(
    Path(__file__).with_name("app.py"),
    secrets=_config.to_streamlit_secrets(),
    routes=create_callback_routes(_config.redirect_uri),
)
```

### 4.3 callback.py

`AZURE_REDIRECT_URI`のパスで受けたリクエストを`/oauth2callback`へ転送するルートを作成する。

```python
def create_callback_routes(redirect_uri: str) -> list[Route]: ...
```

### 4.4 handlers.py

Streamlit統合の認証ハンドラーとUIコンポーネント。

```python
# 認証フロー
def login() -> None: ...   # st.login()
def logout() -> None: ...  # st.logout()


# 認証状態
def is_authenticated() -> bool: ...
def get_current_user() -> UserInfo | None: ...
def get_token_claims() -> dict[str, Any] | None: ...
def require_auth() -> None: ...


# UIコンポーネント
def render_site_header() -> None: ...
def render_sidebar_account() -> None: ...
```

### 4.5 app.py（エントリポイント）

`st.navigation()` APIを使用したルーター兼共通レイアウト。

```python
# 1. 共通レイアウト
render_sidebar_account()
render_site_header()

# 2. ページ定義・ルーティング
pg = st.navigation([...])
pg.run()
```

### 4.6 **init**.py

公開APIのエクスポート。

```python
__all__ = [
    "AuthConfig",
    "get_current_user",
    "get_token_claims",
    "is_authenticated",
    "load_config",
    "login",
    "logout",
    "render_sidebar_account",
    "render_site_header",
    "require_auth",
]
```
