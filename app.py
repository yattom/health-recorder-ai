import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


@app.route('/', methods=['GET'])
def show_form():
    return render_template('index.html')


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
    
    # PRGパターン: POST後はGETにリダイレクト
    return redirect(url_for('show_form'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')