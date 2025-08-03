import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_input_form_page_displays(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'<textarea' in response.data
    assert b'submit' in response.data or '送信'.encode('utf-8') in response.data