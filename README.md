# Entra ID Auth Example

StreamlitアプリケーションにMicrosoft Entra ID（旧Azure AD）認証を組み込むサンプル実装です。

## 機能

- Entra IDによるシングルサインオン（SSO）
- IDトークンからのユーザー情報取得
- ログイン・ログアウト機能
- 認証必須ページのガード機能
- Cookie + HMAC署名によるCSRF対策（Double Submit方式）
- `st.navigation()` APIによるマルチページ構成

## 必要条件

- Python 3.13以上
- uv
- Microsoft Entra IDテナント
- Azure Portalでのアプリ登録

## セットアップ

### 1. 依存関係のインストール

```bash
make install-dev
```

### 2. 環境変数の設定

```bash
cp .env.example .env
```

`.env`ファイルを編集し、Entra IDの設定を入力します。

```bash
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_REDIRECT_URI=http://localhost:8501/callback

# 企業プロキシ環境の場合（任意）
SSL_CA_FILE=/path/to/your/ca.pem
```

> **企業プロキシ環境について**: HTTPSトラフィックを検査する企業プロキシの環境では、
> `SSL_CA_FILE`にプロキシのCA証明書パスを設定してください。
> Python 3.13ではSSL検証が厳格化（`VERIFY_X509_STRICT`）されており、
> AKI拡張のないCA証明書が拒否されるため、本アプリでは`SSL_CA_FILE`設定時に
> このフラグを自動的に無効化します。

### 3. Azure Portalでのアプリ登録

1. Azure Portal → Microsoft Entra ID → アプリの登録 → 新規登録
2. リダイレクトURIに `http://localhost:8501/callback` を追加
3. 「認証」→「IDトークン」を有効化
4. 「証明書とシークレット」→ クライアントシークレットを作成
5. 「APIのアクセス許可」→ `openid`, `profile`, `email` を追加

## 実行

```bash
make run
```

ブラウザで `http://localhost:8501` にアクセスします。

## アーキテクチャ

### マルチページ構成

`st.navigation()` APIを使用し、`app.py` がルーター兼共通レイアウトとして機能します。

```bash
app.py              # エントリポイント（ルーター + 共通レイアウト + OAuthコールバック処理）
pages/
├── home.py         # ホームページ（ログイン/ユーザー情報表示）
├── about.py        # Aboutページ（認証不要）
├── dashboard.py    # ダッシュボード（認証必須）
└── profile.py      # プロファイル（認証必須）
```

### 認証フロー

1. ユーザーがログインボタンを押す
2. Cookie にnonceを設定し、HMAC署名付きstateをパラメーターとしてEntra IDへリダイレクト
3. Entra IDで認証後、認可コード付きでアプリにリダイレクト
4. `app.py` がコールバックを検知（`?code=`）し、state/Cookie検証後にトークン交換
5. セッションに認証情報を保存し、ホームページを表示

## 使用例

### 基本的な使用例（エントリポイント）

```python
import streamlit as st
from entra_id_auth_example import (
    handle_callback,
    render_sidebar_account,
    render_site_header,
)

st.set_page_config(page_title="My App", page_icon="🔐")

# OAuthコールバック処理
if "code" in st.query_params:
    if handle_callback():
        st.rerun()
    else:
        st.stop()

# 共通レイアウト
render_sidebar_account()
render_site_header()

# ページ定義
pg = st.navigation([
    st.Page("pages/home.py", title="Home", default=True),
    st.Page("pages/about.py", title="About"),
])
pg.run()
```

### 認証必須ページ

```python
import streamlit as st
from entra_id_auth_example import get_current_user, require_auth

require_auth()  # 未認証ならここで停止（ログインボタン表示）

user = get_current_user()
st.title(f"{user['name']}のダッシュボード")
```

## 開発

### Makefileコマンド

```bash
make install-dev  # 依存関係インストール
make run          # アプリ実行
make test         # テスト実行
make lint         # リンター実行
make type-check   # 型チェック
make check        # lint + type-check
make clean        # キャッシュ削除
```

## ドキュメント

- [要件定義書](docs/REQUIREMENTS.md)
- [アーキテクチャ設計書](docs/ARCHITECTURE.md)
- [アプリケーション仕様書](docs/SPECIFICATION.md)

## ライセンス

MIT
