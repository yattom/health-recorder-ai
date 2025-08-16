import os
import json
import requests
import sys
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from markdown import convert_markdown

# 設定の読み込み: config.pyがあれば優先、なければ環境変数を使用
try:
    import config
    OLLAMA_URL = config.OLLAMA_URL
    OLLAMA_MODEL = config.OLLAMA_MODEL
    DEFAULT_DATA_DIR = config.DEFAULT_DATA_DIR
    print("config.py から設定を読み込みました（開発環境）", file=sys.stderr)
except ImportError:
    # config.pyがない場合は環境変数から読み込み（デプロイ環境）
    OLLAMA_URL = os.getenv('OLLAMA_URL')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')
    DEFAULT_DATA_DIR = os.getenv('DATA_DIR', 'data')
    
    if not OLLAMA_URL:
        print("ERROR: OLLAMA_URL が設定されていません。", file=sys.stderr)
        print("環境変数 OLLAMA_URL を設定するか、config.py を作成してください。", file=sys.stderr)
        sys.exit(1)
    
    print("環境変数から設定を読み込みました（デプロイ環境）", file=sys.stderr)

app = Flask(__name__)


def get_ollama_config():
    """Ollama設定を取得する"""
    return {
        'url': OLLAMA_URL,
        'model': OLLAMA_MODEL
    }


def get_latest_health_record_time(data_dir=None):
    """最新の健康記録ファイルの時刻を取得する"""
    import re
    
    if data_dir is None:
        data_dir = app.config.get('DATA_DIR', DEFAULT_DATA_DIR)
    
    if not os.path.exists(data_dir):
        return None
    
    # health_record_*.jsonパターンのファイルを探す
    pattern = re.compile(r'^health_record_(\d{8}_\d{6})\.json$')
    files = []
    
    for filename in os.listdir(data_dir):
        match = pattern.match(filename)
        if match:
            timestamp_str = match.group(1)
            files.append(timestamp_str)
    
    if not files:
        return None
    
    # ファイル名でソートして最新を取得
    latest_timestamp = sorted(files)[-1]
    
    # 日時をフォーマット: YYYYMMDD_HHMMSS -> "M月D日 HH:MM"
    try:
        dt = datetime.strptime(latest_timestamp, '%Y%m%d_%H%M%S')
        return f"{dt.month}月{dt.day}日 {dt.hour:02d}:{dt.minute:02d}"
    except ValueError:
        return None


def load_health_records(data_dir=None, days=None, keywords=None):
    """健康記録を読み込む"""
    if data_dir is None:
        data_dir = app.config.get('DATA_DIR', DEFAULT_DATA_DIR)
    
    records = []
    if not os.path.exists(data_dir):
        return records
    
    # 期間フィルタリング用の日付を計算
    cutoff_date = None
    if days is not None:
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
    
    for filename in os.listdir(data_dir):
        if filename.endswith('.json') and filename.startswith('health_record_'):
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    record = json.load(f)
                    
                    # 期間フィルタリング
                    if cutoff_date is not None:
                        record_timestamp = datetime.fromisoformat(record['timestamp'])
                        if record_timestamp < cutoff_date:
                            continue
                    
                    # キーワードフィルタリング
                    if keywords is not None and keywords.strip():
                        # コンマが含まれている場合はコンマ区切り、そうでなければスペース区切り
                        if ',' in keywords:
                            keyword_list = [kw.strip() for kw in keywords.split(',')]
                        else:
                            keyword_list = keywords.split()
                        
                        # いずれかのキーワードが含まれているかチェック（OR条件）
                        if not any(kw in record['health_record'] for kw in keyword_list if kw):
                            continue
                    
                    records.append(record)
            except (json.JSONDecodeError, FileNotFoundError, KeyError, ValueError):
                continue
    
    return records


def create_ollama_payload(message, data_dir=None, days=None, keywords=None):
    """Ollamaに送信するペイロードを作成する"""
    ollama_config = get_ollama_config()
    
    # システムプロンプト
    system_prompt = """あなたは健康管理をサポートするAIアシスタントです。
ユーザーの健康記録に基づいて、親切で正確なアドバイスを提供してください。

IMPORTANT: 必ず日本語で回答してください。英語での回答は絶対に禁止です。
重要: どのような質問でも、必ず日本語で答えてください。"""
    
    # 過去の健康記録を取得
    health_records = load_health_records(data_dir, days, keywords)
    
    # 文脈として健康記録を追加
    context = ""
    if health_records:
        context = "\n\n過去の健康記録:\n"
        for record in health_records[:]:
            context += f"- {record.get('timestamp', '')}: {record.get('health_record', '')}\n"
    
    # 完全なプロンプトを作成
    full_prompt = f"""{system_prompt}{context}

ユーザーの質問: {message}

回答は必ず日本語で行ってください。Answer in Japanese only."""
    
    return {
        'model': ollama_config['model'],
        'prompt': full_prompt,
        'stream': False
    }


@app.route('/', methods=['GET'])
def show_form():
    latest_time = get_latest_health_record_time()
    return render_template('index.html', latest_time=latest_time)


@app.route('/chat', methods=['GET'])
def show_chat():
    return render_template('chat.html')


@app.route('/chat', methods=['POST'])
def chat_with_ai():
    message = request.form['message']
    
    # フィルタリングパラメータを取得
    days_str = request.form.get('days', '')
    keywords = request.form.get('keywords', '')
    
    # days を整数に変換（空文字の場合は None）
    days = None
    if days_str:
        try:
            days = int(days_str)
        except ValueError:
            days = None
    
    # keywords が空文字の場合は None
    if not keywords.strip():
        keywords = None
    
    # Ollama設定を取得
    ollama_config = get_ollama_config()
    
    # フィルタリングパラメータを使ってペイロードを作成
    data_dir = app.config.get('DATA_DIR', DEFAULT_DATA_DIR)
    payload = create_ollama_payload(message, data_dir=data_dir, days=days, keywords=keywords)
    
    # Ollama APIにリクエスト送信
    try:
        response = requests.post(ollama_config['url'], json=payload)
        response.raise_for_status()
        
        ai_response = response.json().get('response', 'AIからの応答を取得できませんでした。')
        
    except requests.exceptions.RequestException as e:
        print(f'{e=}', file=sys.stderr)
        ai_response = "AIサービスに接続できませんでした。"
    
    # AIレスポンスにMarkdown変換を適用
    ai_response_html = convert_markdown(ai_response)
    
    # チャットページにメッセージとレスポンスを表示
    return render_template('chat.html', user_message=message, ai_response=ai_response_html)


@app.route('/', methods=['POST'])
def save_health_record():
    health_record = request.form['health_record']
    
    # データディレクトリの取得（テスト時はTESTING設定から、本番時は設定ファイルから）
    data_dir = app.config.get('DATA_DIR', DEFAULT_DATA_DIR)
    
    # ディレクトリが存在しない場合は作成
    os.makedirs(data_dir, exist_ok=True)
    
    # タイムスタンプ付きファイル名を生成
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'health_record_{timestamp}.json'
    filepath = os.path.join(data_dir, filename)
    
    # JSONデータを作成
    data = {
        'health_record': health_record,
        'timestamp': datetime.now().isoformat()
    }
    
    # JSONファイルに保存
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # PRGパターン: POST後はチャットページにリダイレクト
    return redirect(url_for('show_chat'))


if __name__ == '__main__':
    # 環境変数からポートを取得、デフォルトは5000（開発時）
    port = int(os.getenv('PORT', '5000'))
    app.run(debug=True, host='0.0.0.0', port=port)
