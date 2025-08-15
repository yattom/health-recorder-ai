import pytest
from markdown import convert_markdown


def test_newline_to_br():
    """改行を<br>タグに変換するテスト"""
    input_text = "Hello\nWorld"
    expected = "Hello<br>World"
    result = convert_markdown(input_text)
    assert result == expected


def test_heading_conversion():
    """ヘッダーをHTMLタグに変換するテスト"""
    input_text = "# Heading 1\n## Heading 2\n### Heading 3"
    expected = "<h1>Heading 1</h1><br><h2>Heading 2</h2><br><h3>Heading 3</h3>"
    result = convert_markdown(input_text)
    assert result == expected