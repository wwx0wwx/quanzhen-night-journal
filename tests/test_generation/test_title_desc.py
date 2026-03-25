"""Tests for night_journal.generation.title_desc (offline/mock)"""
import json
import unittest.mock as mock


def _make_mock_api(response_content):
    """Return a mock api_chat that returns given content string."""
    return mock.MagicMock(return_value=response_content)


def test_valid_json_response():
    from night_journal.generation import title_desc as td
    payload = json.dumps({'title': '月下无眠', 'description': '这一夜，灯灭得很早。'})
    with mock.patch.object(td, 'api_chat', _make_mock_api(payload)):
        title, desc = td.generate_title_and_description(
            'http://fake', 'fake-key', 'fake-model',
            '正文示例', [], []
        )
    assert title == '月下无眠'
    assert desc == '这一夜，灯灭得很早。'


def test_json_embedded_in_text():
    from night_journal.generation import title_desc as td
    payload = '好的，以下是结果：\n{"title": "霜色深", "description": "她没有回头。"}'
    with mock.patch.object(td, 'api_chat', _make_mock_api(payload)):
        title, desc = td.generate_title_and_description(
            'http://fake', 'fake-key', 'fake-model',
            '正文示例', [], []
        )
    assert title == '霜色深'
    assert desc == '她没有回头。'


def test_fallback_on_no_json():
    from night_journal.generation import title_desc as td
    with mock.patch.object(td, 'api_chat', _make_mock_api('无法生成')):
        title, desc = td.generate_title_and_description(
            'http://fake', 'fake-key', 'fake-model',
            '正文示例', [], []
        )
    assert title == '灯下未眠'
    assert '灯将尽' in desc


def test_fallback_on_invalid_json():
    from night_journal.generation import title_desc as td
    with mock.patch.object(td, 'api_chat', _make_mock_api('{broken json')):
        title, desc = td.generate_title_and_description(
            'http://fake', 'fake-key', 'fake-model',
            '正文示例', [], []
        )
    assert title == '灯下未眠'


def test_fallback_on_missing_keys():
    from night_journal.generation import title_desc as td
    with mock.patch.object(td, 'api_chat', _make_mock_api('{"other": "value"}')):
        title, desc = td.generate_title_and_description(
            'http://fake', 'fake-key', 'fake-model',
            '正文示例', [], []
        )
    assert title == '灯下未眠'
    assert '灯将尽' in desc
