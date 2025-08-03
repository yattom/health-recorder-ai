import pytest
import os
import tempfile
import shutil
import json
import re
from datetime import datetime
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def temp_data_dir():
    # テスト用の一時ディレクトリを作成
    temp_dir = tempfile.mkdtemp()
    app.config['DATA_DIR'] = temp_dir
    yield temp_dir
    # テスト後にクリーンアップ
    shutil.rmtree(temp_dir)


def test_input_form_page_displays(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'<textarea' in response.data
    assert b'submit' in response.data or '送信'.encode('utf-8') in response.data


def test_css_styling_applied(client):
    response = client.get('/')
    assert response.status_code == 200
    # CSSが適用されているかチェック
    assert b'<link rel="stylesheet"' in response.data or b'<style>' in response.data
    # レスポンシブなviewportメタタグがあるかチェック
    assert b'viewport' in response.data


class Test健康記録保存機能:
    """健康記録保存機能のテストクラス"""
    
    def test_記録送信時のレスポンスが正常(self, client, temp_data_dir):
        """健康記録をPOST送信したときにリダイレクトレスポンスが返ることをテスト（PRGパターン）"""
        health_record = "体重: 70kg\n血圧: 120/80\n調子: 良好"
        
        response = client.post('/', data={'health_record': health_record})
        
        assert response.status_code == 302  # リダイレクト
        assert response.location.endswith('/chat')
    
    def test_記録送信時にファイルが一つ作成される(self, client, temp_data_dir):
        """健康記録をPOST送信したときにファイルが一つ作成されることをテスト"""
        health_record = "体重: 70kg\n血圧: 120/80\n調子: 良好"
        
        client.post('/', data={'health_record': health_record})
        
        files = os.listdir(temp_data_dir)
        assert len(files) == 1
    
    def test_作成されるファイル名の形式が正しい(self, client, temp_data_dir):
        """作成されるファイル名がタイムスタンプ付きの正しい形式であることをテスト"""
        health_record = "体重: 70kg\n血圧: 120/80\n調子: 良好"
        
        client.post('/', data={'health_record': health_record})
        
        files = os.listdir(temp_data_dir)
        filename = files[0]
        
        # ファイル名の形式をテスト: health_record_YYYYMMDD_HHMMSS.json
        pattern = r'^health_record_\d{8}_\d{6}\.json$'
        assert re.match(pattern, filename), f"ファイル名 '{filename}' が期待される形式と一致しません"
    
    def test_保存されたファイルの内容が正しい(self, client, temp_data_dir):
        """保存されたファイルの内容がJSONとして正しく保存されることをテスト"""
        health_record = "体重: 70kg\n血圧: 120/80\n調子: 良好"
        
        client.post('/', data={'health_record': health_record})
        
        files = os.listdir(temp_data_dir)
        filename = files[0]
        
        with open(os.path.join(temp_data_dir, filename), 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        # JSONファイルに健康記録が含まれていることをテスト
        assert 'health_record' in saved_data
        assert saved_data['health_record'] == health_record
        assert 'timestamp' in saved_data


class Testページフロー:
    """ページフロー機能のテストクラス"""
    
    def test_記録送信後にチャットページにリダイレクトする(self, client, temp_data_dir):
        """健康記録送信後にチャットページにリダイレクトされることをテスト"""
        health_record = "体重: 70kg\n血圧: 120/80\n調子: 良好"
        
        response = client.post('/', data={'health_record': health_record})
        
        assert response.status_code == 302  # リダイレクト
        assert response.location.endswith('/chat')
    
    def test_チャットページが正しく表示される(self, client):
        """チャットページが正しく表示されることをテスト"""
        response = client.get('/chat')
        
        assert response.status_code == 200
        assert b'chat' in response.data or 'チャット'.encode('utf-8') in response.data


class TestAIチャット機能:
    """AIチャット機能のテストクラス"""
    
    def test_チャットページに入力フォームがある(self, client):
        """チャットページにメッセージ入力フォームがあることをテスト"""
        response = client.get('/chat')
        
        assert response.status_code == 200
        assert b'<form' in response.data
        assert b'name="message"' in response.data
        assert b'method="post"' in response.data.lower()
    
    def test_チャットメッセージをPOSTできる(self, client):
        """チャットメッセージをPOSTして適切なレスポンスが返ることをテスト"""
        message = "体重について教えて"
        
        response = client.post('/chat', data={'message': message})
        
        assert response.status_code == 200
        assert 'チャット'.encode('utf-8') in response.data
    
    def test_AIからのレスポンスが表示される(self, client):
        """AIからのレスポンスがページに表示されることをテスト"""
        message = "体重について教えて"
        
        response = client.post('/chat', data={'message': message})
        
        assert response.status_code == 200
        # AIからの何らかのレスポンスが含まれている
        assert b'AI' in response.data or 'AI'.encode('utf-8') in response.data


class Test設定ファイル機能:
    """設定ファイル機能のテストクラス"""
    
    def test_設定ファイルからOllama設定を読み込む(self):
        """config.pyからOllamaのURLとモデル名が読み込まれることをテスト"""
        from app import get_ollama_config
        
        config = get_ollama_config()
        
        assert 'url' in config
        assert 'model' in config
        assert config['url'].startswith('http')
        assert isinstance(config['model'], str)
    
    def test_設定値が正しく使用される(self, client):
        """設定されたOllama設定が実際に使用されることをテスト"""
        from app import get_ollama_config
        
        config = get_ollama_config()
        
        # 設定が読み込まれていることを確認
        assert config['url'] is not None
        assert config['model'] is not None


class TestOllamaペイロード機能:
    """Ollamaペイロード機能のテストクラス"""
    
    def test_基本ペイロード生成(self):
        """基本的なペイロードが正しく生成されることをテスト"""
        from app import create_ollama_payload
        
        message = "体重について教えて"
        payload = create_ollama_payload(message)
        
        assert 'model' in payload
        assert 'prompt' in payload
        assert 'stream' in payload
        assert payload['model'] == 'llama3'
        assert payload['stream'] is False
        assert message in payload['prompt']
    
    def test_システムプロンプト付きペイロード生成(self):
        """システムプロンプトが含まれたペイロードが生成されることをテスト"""
        from app import create_ollama_payload
        
        message = "体重について教えて"
        payload = create_ollama_payload(message)
        
        # システムプロンプトに日本語指定が含まれていることを確認
        assert '日本語' in payload['prompt']
        assert 'アシスタント' in payload['prompt']  # システムプロンプトの存在を確認
    
    def test_健康記録文脈付きペイロード生成(self, temp_data_dir):
        """過去の健康記録が文脈として含まれることをテスト"""
        from app import create_ollama_payload
        
        # テスト用の健康記録ファイルを作成
        test_record = {
            "health_record": "体重: 70kg\n血圧: 120/80",
            "timestamp": "2025-08-01T10:00:00"
        }
        
        import json
        import os
        filename = os.path.join(temp_data_dir, "health_record_20250801_100000.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(test_record, f, ensure_ascii=False)
        
        message = "最近の体重はどうですか？"
        payload = create_ollama_payload(message, data_dir=temp_data_dir)
        
        # 過去の記録が含まれていることを確認
        assert '70kg' in payload['prompt']
        assert '120/80' in payload['prompt']
    
