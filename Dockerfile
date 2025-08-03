# Python 3.9のslimイメージを使用（軽量かつ必要な機能を含む）
FROM python:3.9-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetryをインストール
RUN pip install poetry

# Poetry設定（仮想環境を作らずにグローバルにインストール）
RUN poetry config virtualenvs.create false

# pyproject.tomlとpoetry.lockをコピー
COPY pyproject.toml poetry.lock ./

# 依存関係をインストール（プロダクション用のみ）
RUN poetry install --only=main

# アプリケーションコードをコピー
COPY . .

# 非rootユーザーを作成してセキュリティを向上
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# データディレクトリを作成
RUN mkdir -p /app/data

# ポート5000を公開
EXPOSE 5000

# 本番環境用の設定でFlaskアプリを起動
CMD ["python", "-c", "import app; app.app.run(host='0.0.0.0', port=5000, debug=False)"]