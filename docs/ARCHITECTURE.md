# Streamlit Entra ID Authentication - アーキテクチャ設計書

| 項目 | 内容 |
|------|------|
| バージョン | 0.1.0（Draft） |
| 作成日 | 2026年1月24日 |

---

## 1. システム構成

### 1.1 認証フロー

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Browser   │      │  Streamlit  │      │  Entra ID   │
│             │      │    App      │      │             │
└──────┬──────┘      └──────┬──────┘      └──────┬──────┘
       │                    │                    │
       │  1. アクセス       │                    │
       │───────────────────>│                    │
       │                    │                    │
       │  2. 未認証→リダイレクト                 │
       │<───────────────────│                    │
       │                    │                    │
       │  3. 認証リクエスト                      │
       │────────────────────────────────────────>│
       │                    │                    │
       │  4. ログイン画面                        │
       │<────────────────────────────────────────│
       │                    │                    │
       │  5. 認証情報入力                        │
       │────────────────────────────────────────>│
       │                    │                    │
       │  6. 認可コード付きリダイレクト          │
       │<────────────────────────────────────────│
       │                    │                    │
       │  7. コールバック   │                    │
       │───────────────────>│                    │
       │                    │                    │
       │                    │  8. トークン交換   │
       │                    │───────────────────>│
       │                    │                    │
       │                    │  9. ID/Access Token│
       │                    │<───────────────────│
       │                    │                    │
       │  10. 認証完了      │                    │
       │<───────────────────│                    │
       │                    │                    │
```

### 1.2 技術スタック

| コンポーネント | 技術 |
|---------------|------|
| フレームワーク | Streamlit |
| 認証プロトコル | OpenID Connect (OIDC) |
| IdP | Microsoft Entra ID |
| OIDCライブラリ | `msal` (Microsoft Authentication Library) |
| セッション管理 | `st.session_state` |

---

## 2. ディレクトリ構成

```
streamlit-entra-auth/
├── src/
│   └── streamlit_entra_auth/
│       ├── __init__.py        # 公開関数のエクスポート
│       ├── config.py          # 設定管理
│       ├── client.py          # MSALクライアント
│       ├── handlers.py        # 認証ハンドラ
│       ├── app.py             # メインアプリケーション
│       └── pages/
│           ├── dashboard.py   # 認証必須ページ例
│           └── profile.py     # プロファイルページ例
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   └── test_handlers.py
├── docs/
│   ├── requirements.md        # 要件定義書
│   └── architecture.md        # 本ドキュメント
├── .env.example               # 環境変数テンプレート
├── .python-version            # Pythonバージョン指定（uv/pyenv用）
├── pyproject.toml             # プロジェクト設定
├── uv.lock                    # 依存関係ロックファイル
├── README.md
└── LICENSE
```

### 2.1 src layoutを採用する理由

- ローカルソースの誤importを防止
- `pip install -e .` によるeditable installを強制
- テスト時にインストール済みパッケージをテストすることを保証
- PyPA、pytest等の推奨構成に準拠

---

## 3. インターフェース仕様

### 3.1 設定

環境変数または`.env`ファイルで設定を管理する。

| 環境変数 | 説明 | 例 |
|---------|------|-----|
| `AZURE_CLIENT_ID` | アプリケーション（クライアント）ID | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `AZURE_CLIENT_SECRET` | クライアントシークレット | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `AZURE_TENANT_ID` | ディレクトリ（テナント）ID | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `AZURE_REDIRECT_URI` | リダイレクトURI | `http://localhost:8501/callback` |

### 3.2 公開関数

#### login()

Entra IDのログインページにリダイレクトする。

```python
def login() -> None:
    """認証フローを開始し、Entra IDにリダイレクト"""
    ...
```

#### logout()

セッションをクリアし、Entra IDからログアウトする。

```python
def logout() -> None:
    """セッションをクリアし、Entra IDのログアウトエンドポイントにリダイレクト"""
    ...
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
    ...
```

#### is_authenticated()

現在の認証状態を確認する。

```python
def is_authenticated() -> bool:
    """認証済みかどうかを返す"""
    return st.session_state.get("authenticated", False)
```

#### get_current_user()

現在のユーザー情報を取得する。

```python
def get_current_user() -> dict | None:
    """
    認証済みユーザーの情報を返す
    
    Returns:
        dict: {"id": str, "name": str, "email": str}
        None: 未認証の場合
    """
    ...
```

#### require_auth()

認証を必須とするページガード関数。

```python
def require_auth() -> None:
    """
    未認証の場合、ログインページにリダイレクトまたはエラー表示してst.stop()
    """
    ...
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
    
    @property
    def authority(self) -> str:
        return f"https://login.microsoftonline.com/{self.tenant_id}"
```

### 4.2 client.py

MSALクライアントのラッパー。

```python
class EntraAuthClient:
    def __init__(self, config: AuthConfig): ...
    def get_auth_url(self, state: str) -> str: ...
    def acquire_token_by_code(self, code: str) -> dict: ...
```

### 4.3 handlers.py

Streamlit統合の認証ハンドラ。

```python
def login() -> None: ...
def logout() -> None: ...
def handle_callback() -> bool: ...
def is_authenticated() -> bool: ...
def get_current_user() -> dict | None: ...
def require_auth() -> None: ...
```

### 4.4 __init__.py

公開APIのエクスポート。

```python
from .handlers import (
    login,
    logout,
    handle_callback,
    is_authenticated,
    get_current_user,
    require_auth,
)

__all__ = [
    "login",
    "logout",
    "handle_callback",
    "is_authenticated",
    "get_current_user",
    "require_auth",
]
```
