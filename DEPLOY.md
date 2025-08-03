# QNAP NAS デプロイガイド

## 前提条件

1. QNAP NASでContainer StationまたはDocker CEがインストール済み
2. OllamaがQNAP NAS上で動作している（または外部サーバーでアクセス可能）
3. ローカル開発マシンからNASへのSSH接続が可能
4. ローカルマシンにDockerがインストール済み

## 簡単デプロイ（推奨）

自動デプロイスクリプトを使用：

```bash
# デプロイスクリプトを実行
./deploy-to-nas.sh 192.168.1.100

# 完了後、NASにSSH接続してコンテナを起動
ssh admin@192.168.1.100
cd /share/Container/health-recorder

# 環境変数を設定してコンテナ起動
OLLAMA_URL=http://your-ollama-host:11434/api/generate \
OLLAMA_MODEL=llama3 \
docker-compose up -d
```

## 手動デプロイ

### 1. ローカルでDockerイメージをビルド

```bash
# プロジェクトディレクトリで実行
docker build -t health-recorder-ai:latest .

# イメージをエクスポート
docker save health-recorder-ai:latest -o health-recorder-ai.tar
```

### 2. NASにファイルを転送

```bash
# NAS上にディレクトリ作成
ssh admin@your-nas-ip "mkdir -p /share/Container/health-recorder"

# 必要ファイルを転送
scp health-recorder-ai.tar admin@your-nas-ip:/share/Container/health-recorder/
scp docker-compose.yml admin@your-nas-ip:/share/Container/health-recorder/
```

### 3. NAS上でセットアップ

```bash
# NASにSSH接続
ssh admin@your-nas-ip

# デプロイディレクトリに移動
cd /share/Container/health-recorder

# Dockerイメージをロード
docker load -i health-recorder-ai.tar

# 環境変数を設定してコンテナ起動
OLLAMA_URL=http://your-ollama-host:11434/api/generate \
OLLAMA_MODEL=llama3 \
docker-compose up -d
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

## 更新手順

新しいバージョンをデプロイする場合：

```bash
# 1. 自動デプロイスクリプトを再実行
./deploy-to-nas.sh your-nas-ip

# 2. NAS上でコンテナを再起動
ssh admin@your-nas-ip
cd /share/Container/health-recorder
OLLAMA_URL=http://your-ollama-host:11434/api/generate \
OLLAMA_MODEL=llama3 \
docker-compose up -d
```

または手動での更新：

```bash
# 1. 新しいイメージをビルド・エクスポート
docker build -t health-recorder-ai:latest .
docker save health-recorder-ai:latest -o health-recorder-ai.tar

# 2. NASに転送
scp health-recorder-ai.tar admin@your-nas-ip:/share/Container/health-recorder/

# 3. NAS上で更新
ssh admin@your-nas-ip
cd /share/Container/health-recorder
docker-compose down
docker load -i health-recorder-ai.tar
OLLAMA_URL=http://your-ollama-host:11434/api/generate \
OLLAMA_MODEL=llama3 \
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