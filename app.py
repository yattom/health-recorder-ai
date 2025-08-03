import os
import json
import requests
import sys
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

try:
    import config
except ImportError:
    print("ERROR: config.py が見つかりません。", file=sys.stderr)
    print("config.py.example をコピーして config.py を作成し、設定を行ってください。", file=sys.stderr)
    sys.exit(1)

app = Flask(__name__)


def get_ollama_config():
    """Ollama設定を取得する"""
    return {
        'url': config.OLLAMA_URL,
        'model': config.OLLAMA_MODEL
    }


def load_health_records(data_dir=None, days=None, keywords=None):
    """健康記録を読み込む"""
    if data_dir is None:
        data_dir = app.config.get('DATA_DIR', config.DEFAULT_DATA_DIR)
    
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
        for record in health_records[-5:]:  # 最新5件
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
    return render_template('index.html')


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
    data_dir = app.config.get('DATA_DIR', config.DEFAULT_DATA_DIR)
    payload = create_ollama_payload(message, data_dir=data_dir, days=days, keywords=keywords)
    
    # Ollama APIにリクエスト送信
    try:
        response = requests.post(ollama_config['url'], json=payload)
        response.raise_for_status()
        
        ai_response = response.json().get('response', 'AIからの応答を取得できませんでした。')
        
    except requests.exceptions.RequestException as e:
        print(f'{e=}', file=sys.stderr)
        ai_response = "AIサービスに接続できませんでした。"
    
    # チャットページにメッセージとレスポンスを表示
    return render_template('chat.html', user_message=message, ai_response=ai_response)


@app.route('/', methods=['POST'])
def save_health_record():
    health_record = request.form['health_record']
    
    # データディレクトリの取得（テスト時はTESTING設定から、本番時は設定ファイルから）
    data_dir = app.config.get('DATA_DIR', config.DEFAULT_DATA_DIR)
    
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
    app.run(debug=True, host='0.0.0.0')