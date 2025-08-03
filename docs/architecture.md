# 健康記録Webサービス アーキテクチャ設計書

## システム全体構成

```
[スマートフォン/PC ブラウザ] 
    ↓ HTTP
[Docker Container: Webアプリ]
    ↓ HTTP API
[ローカルLLM (Ollama)]

[永続ストレージ (マウントボリューム)]
```

## コンポーネント設計

### 1. Webアプリケーション (Docker Container)

#### 1.1 バックエンド (Python)
- **フレームワーク**: Flask または FastAPI
- **構成**:
  - `app.py`: メインアプリケーション
  - `models/`: データモデル（ファイル操作）
  - `services/`: ビジネスロジック
    - `record_service.py`: 記録の保存・取得
    - `ai_service.py`: LLM連携
    - `guidance_service.py`: 入力ガイダンス生成
  - `routes/`: APIエンドポイント
    - `record_routes.py`: 記録関連API
    - `chat_routes.py`: AIチャット関連API

#### 1.2 フロントエンド (JavaScript)
- **技術**: Vanilla JavaScript + HTML/CSS
- **構成**:
  - `static/index.html`: メインページ
  - `static/js/app.js`: メインアプリケーション
  - `static/js/api.js`: API通信
  - `static/css/style.css`: スタイル
- **機能**:
  - 記録入力フォーム
  - ガイダンス表示
  - AIチャットインターフェース

### 2. データストレージ

#### 2.1 ファイル構造
```
/data/
  ├── records/
  │   ├── 2024/
  │   │   ├── 01/
  │   │   │   ├── 20240101_143022_record.txt
  │   │   │   └── 20240101_203015_record.txt
  │   │   └── 02/
  │   └── 2025/
  ├── chat_history/
  │   ├── 2024/
  │   │   └── 01/
  │   │       ├── 20240101_143500_chat.json
  │   │       └── 20240101_204000_chat.json
  │   └── 2025/
  └── guidance/
      └── recent_patterns.json
```

#### 2.2 ファイル形式
- **記録ファイル**: プレーンテキスト（.txt）
  ```
  timestamp: 2024-01-01 14:30:22
  今日は7時間寝た。朝のランニング30分。気分は普通
  ```

- **チャット履歴**: JSON形式
  ```json
  {
    "timestamp": "2024-01-01T14:35:00Z",
    "user_message": "最近の睡眠パターンはどう？",
    "ai_response": "過去1週間の記録を見ると...",
    "context_files": ["20240101_143022_record.txt", ...]
  }
  ```

### 3. 外部連携

#### 3.1 ローカルLLM (Ollama)
- **接続**: HTTP API（例: http://localhost:11434）
- **通信形式**: REST API / JSON
- **モデル**: 設定可能（例: llama3, mistral）

## API設計

### 3.1 記録関連API
- `POST /api/records` - 新しい記録を保存
- `GET /api/records` - 記録一覧取得（ページネーション対応）
- `GET /api/guidance` - 入力ガイダンス取得

### 3.2 AIチャット関連API
- `POST /api/chat` - AIとのチャット
- `GET /api/chat/history` - チャット履歴取得（将来実装）

## デプロイメント設計

### 4.1 Docker構成
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
VOLUME ["/data"]
CMD ["python", "app.py"]
```

### 4.2 docker-compose.yml
```yaml
version: '3.8'
services:
  health-recorder:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/data
    environment:
      - OLLAMA_URL=http://host.docker.internal:11434
```

## セキュリティ考慮事項

### 5.1 データ保護
- ローカル環境のみでの運用
- ファイルシステムレベルでのアクセス制御
- 機密情報の暗号化は当面不要（プライベート利用）

### 5.2 入力検証
- ファイルパスインジェクション対策
- XSS対策（出力エスケープ）
- 入力サイズ制限

## 開発・運用考慮事項

### 6.1 開発環境
- Python 仮想環境使用
- 開発用Dockerfileとproduction用の分離
- ローカルでのOllama動作確認

### 6.2 モニタリング
- アプリケーションログ
- ファイルシステム使用量監視
- LLM API応答時間監視

### 6.3 バックアップ
- `/data` ディレクトリの定期バックアップ推奨
- 記録データの重要度に応じたバックアップ戦略