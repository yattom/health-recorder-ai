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


@app.route('/', methods=['GET'])
def show_form():
    return render_template('index.html')


@app.route('/chat', methods=['GET'])
def show_chat():
    return render_template('chat.html')


@app.route('/chat', methods=['POST'])
def chat_with_ai():
    message = request.form['message']
    
    # Ollama設定を取得
    ollama_config = get_ollama_config()
    
    # Ollama APIにリクエスト送信
    try:
        payload = {
            "model": ollama_config['model'],
            "prompt": message,
            "stream": False
        }
        
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