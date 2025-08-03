import os
import json
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


@app.route('/', methods=['GET'])
def show_form():
    return render_template('index.html')


@app.route('/chat', methods=['GET'])
def show_chat():
    return render_template('chat.html')


@app.route('/chat', methods=['POST'])
def chat_with_ai():
    message = request.form['message']
    
    # Ollama APIにリクエスト送信
    try:
        ollama_url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3",
            "prompt": message,
            "stream": False
        }
        
        response = requests.post(ollama_url, json=payload)
        response.raise_for_status()
        
        ai_response = response.json().get('response', 'AIからの応答を取得できませんでした。')
        
    except requests.exceptions.RequestException:
        ai_response = "AIサービスに接続できませんでした。"
    
    # チャットページにメッセージとレスポンスを表示
    return render_template('chat.html', user_message=message, ai_response=ai_response)


@app.route('/', methods=['POST'])
def save_health_record():
    health_record = request.form['health_record']
    
    # データディレクトリの取得（テスト時はTESTING設定から、本番時はデフォルト）
    data_dir = app.config.get('DATA_DIR', 'data')
    
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