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