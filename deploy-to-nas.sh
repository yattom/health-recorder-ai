#!/bin/bash

# QNAP NAS デプロイスクリプト
# 使用方法: ./deploy-to-nas.sh <NAS_IP_ADDRESS>

set -e

# 引数チェック
if [ $# -ne 1 ]; then
    echo "使用方法: $0 <NAS_IP_ADDRESS>"
    echo "例: $0 192.168.1.100"
    exit 1
fi

NAS_IP=$1
NAS_USER=${NAS_USER:-admin}
DEPLOY_DIR="/share/Container/health-recorder"

echo "=== QNAP NAS デプロイ開始 ==="
echo "NAS IP: $NAS_IP"
echo "NAS User: $NAS_USER"
echo "Deploy Dir: $DEPLOY_DIR"

# 1. ローカルでDockerイメージをビルド
echo "1. Dockerイメージをビルド中..."
docker build -t health-recorder-ai:latest .

# 2. イメージをtar形式でエクスポート
echo "2. イメージをエクスポート中..."
docker save health-recorder-ai:latest -o health-recorder-ai.tar

# 3. NASにディレクトリを作成
echo "3. NAS上にディレクトリを作成中..."
ssh $NAS_USER@$NAS_IP "mkdir -p $DEPLOY_DIR"

# 4. 必要なファイルをNASに転送
echo "4. ファイルをNASに転送中..."
scp health-recorder-ai.tar $NAS_USER@$NAS_IP:$DEPLOY_DIR/
scp docker-compose.yml $NAS_USER@$NAS_IP:$DEPLOY_DIR/
scp DEPLOY.md $NAS_USER@$NAS_IP:$DEPLOY_DIR/

# 5. NAS上でDockerイメージをロード
echo "5. NAS上でDockerイメージをロード中..."
ssh $NAS_USER@$NAS_IP "cd $DEPLOY_DIR && docker load -i health-recorder-ai.tar"

# 6. 既存のコンテナを停止・削除
echo "6. 既存のコンテナを停止中..."
ssh $NAS_USER@$NAS_IP "cd $DEPLOY_DIR && docker-compose down || true"

# 7. ローカルのtarファイルを削除
echo "7. ローカルの一時ファイルを削除中..."
rm health-recorder-ai.tar

echo "=== デプロイ完了 ==="
echo ""
echo "次の手順:"
echo "1. NASにSSH接続: ssh $NAS_USER@$NAS_IP"
echo "2. ディレクトリ移動: cd $DEPLOY_DIR"
echo "3. 環境変数を設定してコンテナ起動:"
echo "   OLLAMA_URL=http://your-ollama-host:11434/api/generate \\"
echo "   OLLAMA_MODEL=llama3 \\"
echo "   docker-compose up -d"
echo ""
echo "アクセス: http://$NAS_IP:5000"