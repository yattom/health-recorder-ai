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
- **フレームワーク**: ✅ Flask（実装済み）
- **構成**:
  - `app.py`: ✅ メインアプリケーション（実装済み）
    - 記録保存、チャット機能、フィルタリング機能を統合
  - `config.py`: ✅ 設定ファイル（Ollama URL、モデル名等）
  - `test_app.py`: ✅ 包括的テストスイート（TDD approach）
- **実装済み機能**:
  - ファイルシステムベースの記録保存・読み込み
  - Ollama LLM連携（日本語システムプロンプト付き）
  - 期間・キーワードフィルタリング機能

#### 1.2 フロントエンド
- **技術**: ✅ HTML/CSS（実装済み）
- **構成**:
  - `templates/index.html`: ✅ 記録入力ページ（実装済み）
  - `templates/chat.html`: ✅ AIチャットページ（実装済み）
  - `static/styles.css`: ✅ 基本スタイル（実装済み）
- **実装済み機能**:
  - ✅ 記録入力フォーム（大きなテキストエリア）
  - ✅ AIチャットインターフェース
  - ✅ 期間指定UI（1週間・1ヶ月ドロップダウン）
  - ✅ キーワードフィルタリングUI（テキスト入力）

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

#### 2.2 ファイル形式（実装済み）
- **記録ファイル**: ✅ JSON形式（.json）
  ```json
  {
    "health_record": "今日は7時間寝た。朝のランニング30分。気分は普通",
    "timestamp": "2024-01-01T14:30:22.123456"
  }
  ```
  - ファイル名: `health_record_YYYYMMDD_HHMMSS.json`

- **チャット履歴**: 🚧 未実装（次期実装予定）
  ```json
  {
    "timestamp": "2024-01-01T14:35:00Z",
    "user_message": "最近の睡眠パターンはどう？",
    "ai_response": "過去1週間の記録を見ると...",
    "context_records": ["health_record_20240101_143022.json", ...]
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