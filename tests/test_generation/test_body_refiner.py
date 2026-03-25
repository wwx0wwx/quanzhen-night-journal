"""Tests for night_journal.generation.body_refiner (offline/mock)"""
import unittest.mock as mock


def test_refine_returns_string():
    from night_journal.generation import body_refiner as br
    refined = '削薄后的正文'
    with mock.patch.object(br, 'api_chat', mock.MagicMock(return_value=refined)):
        result = br.refine_body('http://fake', 'fake-key', 'fake-model', '原始正文')
    assert result == refined


def test_refine_passes_body_in_prompt():
    from night_journal.generation import body_refiner as br
    captured = {}
    def fake_api(base_url, api_key, model, messages, **kwargs):
        captured['messages'] = messages
        return '润色后'
    with mock.patch.object(br, 'api_chat', fake_api):
        br.refine_body('http://fake', 'fake-key', 'fake-model', '今夜正文内容')
    user_content = captured['messages'][1]['content']
    assert '今夜正文内容' in user_content


def test_refine_uses_low_temperature():
    from night_journal.generation import body_refiner as br
    captured = {}
    def fake_api(base_url, api_key, model, messages, temperature=0.8, **kwargs):
        captured['temperature'] = temperature
        return '润色后'
    with mock.patch.object(br, 'api_chat', fake_api):
        br.refine_body('http://fake', 'fake-key', 'fake-model', '正文')
    assert captured['temperature'] <= 0.5


def test_refine_system_prompt_mentions_refine():
    from night_journal.generation import body_refiner as br
    captured = {}
    def fake_api(base_url, api_key, model, messages, **kwargs):
        captured['messages'] = messages
        return '润色后'
    with mock.patch.object(br, 'api_chat', fake_api):
        br.refine_body('http://fake', 'fake-key', 'fake-model', '正文')
    system_content = captured['messages'][0]['content']
    assert '润色' in system_content or '削薄' in system_content
