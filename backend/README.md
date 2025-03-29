# Backend Service

This is the backend service for the Todo application, built with FastAPI and Supabase.

## Features

- RESTful API endpoints
- Supabase integration
- Authentication and authorization
- CORS support
- HTTPS enabled

## Development

The service is containerized using Docker and can be run using docker-compose:

```bash
docker compose up backend
```

## Environment Variables

Copy the `.env.sample` file to `.env` and configure the following variables:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase service role key
- `SUPABASE_JWT_SECRET`: Your Supabase JWT secret
- `API_HOST`: API host (default: 0.0.0.0)
- `API_PORT`: API port (default: 8000)
- `CORS_ORIGINS`: Allowed CORS origins

## 機能

- Supabaseによるユーザー認証
- ユーザー管理（追加・更新・削除）
- Todoアイテム管理（追加・更新・削除・一覧取得）
- SQLAlchemyによるORM
- Alembicによるデータベースマイグレーション

## 技術スタック

- FastAPI: Webフレームワーク
- Supabase: 認証とデータベース
- SQLAlchemy: ORM
- Alembic: マイグレーション
- Python 3.12

## アーキテクチャ

このアプリケーションは以下のレイヤーアーキテクチャに従っています：

1. **コントローラー層** (API Endpoints): HTTPリクエストの処理とレスポンス生成を担当
2. **サービス層** (Services): ビジネスロジックの実装を担当
3. **リポジトリ層** (Repositories): データアクセスロジックを担当
4. **モデル層** (Models): データモデルとスキーマを担当

### リポジトリパターン

このアプリではリポジトリパターンを採用しており、以下の利点があります：

- データソース（SupabaseとローカルDB）へのアクセスを抽象化
- サービス層をデータアクセスの詳細から切り離し
- テストの容易性向上（リポジトリをモックできる）
- コードの再利用性向上

主なリポジトリクラス：

- `SupabaseUserRepository`: Supabaseユーザー管理操作
- `UserRepository`: ローカルデータベースのユーザー操作
- `ItemRepository`: ローカルデータベースのアイテム操作

## セットアップ

### 1. Pythonバージョンの確認

```bash
python --version  # 3.12以上が必要
```

### 2. 環境変数の設定

`.env`ファイルを作成し、以下の設定を行います：

```
# Supabase設定
SUPABASE_URL=あなたのSupabaseのURL
SUPABASE_KEY=あなたのSupabaseのキー

# データベース設定
DATABASE_URL=あなたのデータベースURL

# アプリケーション設定
DEBUG=True
ENVIRONMENT=development
```

### 3. 依存関係のインストール

```bash
pip install -e .
```

### 4. データベースマイグレーションの実行

```bash
alembic upgrade head
```

### 5. サーバーの起動

```bash
uvicorn app.main:app --reload
```

## APIエンドポイント

- `POST /api/auth/register`: 新規ユーザー登録
- `POST /api/auth/token`: ログイン（トークン取得）
- `GET /api/users/me`: 現在のユーザー情報取得
- `PUT /api/users/me`: ユーザー情報更新
- `DELETE /api/users/me`: ユーザー削除
- `GET /api/items`: Todoアイテム一覧取得
- `POST /api/items`: 新規Todoアイテム作成
- `GET /api/items/{item_id}`: 特定のTodoアイテム取得
- `PUT /api/items/{item_id}`: Todoアイテム更新
- `DELETE /api/items/{item_id}`: Todoアイテム削除

## プロジェクト構成

```
backend/
├── alembic/             # マイグレーションファイル
├── app/
│   ├── api/             # APIエンドポイント (コントローラー層)
│   │   ├── endpoints/   # 各エンドポイント実装
│   ├── core/            # コア機能
│   ├── models/          # SQLAlchemyモデル (モデル層)
│   ├── schemas/         # Pydanticスキーマ (モデル層)
│   ├── services/        # ビジネスロジック (サービス層)
│   ├── repositories/    # データアクセスロジック (リポジトリ層)
│   └── main.py          # アプリケーションエントリーポイント
├── .env                 # 環境変数（gitignore対象）
├── .env.sample          # 環境変数サンプル
├── alembic.ini          # Alembic設定
└── pyproject.toml       # プロジェクト設定
``` 