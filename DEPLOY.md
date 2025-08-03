# QNAP NAS デプロイガイド

## 前提条件

1. QNAP NASでContainer Stationがインストール済み
2. OllamaがQNAP NAS上で動作している（または外部サーバーでアクセス可能）
3. インターネット接続（Docker Hubからイメージをダウンロードするため）

## デプロイ方法

### 方法A: Container Station UI（推奨）

Container StationのGUIを使用してコンテナを作成する最も簡単な方法：

#### 1. Container Stationでコンテナ作成
1. QNAP Container Stationを開く
2. 「Create」→「Container」を選択
3. 「Search Docker Hub」で `yattom/health-recorder-ai` を検索してダウンロード

#### 2. 環境変数設定
「Advanced Settings」→「Environment」で以下を設定：
- `OLLAMA_URL`: `http://your-ollama-host:11434/api/generate`
- `OLLAMA_MODEL`: `llama3`

#### 3. ボリュームマウント設定
「Advanced Settings」→「Volume」で：
- Host Path: `/share/Container/health-recorder-data`
- Mount Path: `/app/data`

#### 4. ネットワーク設定
- Port Forwarding: `5000:5000`

### 方法B: Docker Compose使用

NAS上に `docker-compose.yml` ファイルを配置する必要があります：

```bash
# SSH経由でファイルを作成、またはFile Stationでアップロード
# 場所: /share/Container/health-recorder/docker-compose.yml
```

#### 2. SSH経由でDockerコンテナ起動

```bash
# NASにSSH接続
ssh admin@your-nas-ip

# プロジェクトディレクトリに移動
cd /share/Container/health-recorder

# 環境変数を設定してコンテナを起動
OLLAMA_URL=http://your-ollama-host:11434/api/generate \
OLLAMA_MODEL=llama3 \
docker-compose up -d

# ログ確認
docker-compose logs -f
```

## アクセス確認

ブラウザで以下にアクセス：
```
http://your-nas-ip:5000
```

## 設定オプション

### Ollama接続設定

環境に応じてOLLAMA_URLを調整：

```yaml
# 同一NAS内のOllama（推奨）
- OLLAMA_URL=http://localhost:11434/api/generate

# 別サーバーのOllama
- OLLAMA_URL=http://192.168.1.200:11434/api/generate

# Docker内部ネットワーク経由
- OLLAMA_URL=http://ollama:11434/api/generate
```

### データ永続化設定

デフォルトではDockerボリュームを使用。ホストディレクトリにマウントする場合：

```yaml
volumes:
  - /share/Container/health-recorder-data:/app/data
```

### ポート変更

デフォルトポート5000を変更する場合：

```yaml
ports:
  - "8080:5000"  # 外部ポート8080に変更
```

## トラブルシューティング

### Ollamaに接続できない

1. Ollamaサービスが起動しているか確認
2. ファイアウォール設定を確認
3. docker-compose.ymlのOLLAMA_URLが正しいか確認

### データが保存されない

1. データディレクトリの権限を確認
2. ボリュームマウントが正しいか確認

### コンテナが起動しない

```bash
# ログ確認
docker-compose logs health-recorder

# コンテナの状態確認
docker-compose ps
```

## イメージビルドとアップロード（開発者向け）

新しいバージョンをリリースする場合：

```bash
# ローカルでイメージをビルド
docker build -t yattom/health-recorder-ai:latest .

# Docker Hubにプッシュ
docker push yattom/health-recorder-ai:latest
```

またはGitHub Actionsで自動ビルド（`.github/workflows/docker-build.yml`設定済み）

## 更新手順

Container Station UIの場合：
1. コンテナを停止
2. 最新イメージをpull
3. コンテナを再作成

SSH経由の場合：
```bash
# 最新イメージを取得
docker-compose pull

# コンテナを再起動
docker-compose up -d
```

## バックアップ

データボリュームのバックアップ：

```bash
# データボリュームの場所を確認
docker volume inspect health-recorder_health_data

# バックアップ作成
docker run --rm -v health-recorder_health_data:/data -v $(pwd):/backup ubuntu tar czf /backup/health-data-backup.tar.gz -C /data .
```

## セキュリティ考慮事項

1. NAS管理者以外からのアクセス制御
2. HTTPSリバースプロキシの設定（推奨）
3. 定期的なバックアップ実行
4. ログ監視の設定