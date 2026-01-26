# Entra ID Auth Example

StreamlitアプリケーションにMicrosoft Entra ID（旧Azure AD）認証を組み込むサンプル実装です。

## 機能

- Entra IDによるシングルサインオン（SSO）
- IDトークンからのユーザー情報取得
- ログイン・ログアウト機能
- 認証必須ページのガード機能

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
```

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

## 使用例

### 基本的な使用例

```python
import streamlit as st
from entra_id_auth_example import (
    get_current_user,
    handle_callback,
    is_authenticated,
    login,
    logout,
)

# コールバック処理（URLに?code=...がある場合）
handle_callback()

# メインページ
if is_authenticated():
    user = get_current_user()
    st.write(f"ようこそ、{user['name']}さん")

    if st.button("ログアウト"):
        logout()
else:
    st.write("ログインしてください")
    if st.button("ログイン"):
        login()
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

## ライセンス

MIT
