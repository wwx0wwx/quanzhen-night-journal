"""Integration tests for night_journal.application (LLM mocked)"""
import os
import json
import pytest
import unittest.mock as mock
from pathlib import Path

LONG_BODY = ('廊下起了风。\n属下站在原处，没有动。\n灯的影子贴着墙，像一个旧日的问题，始终没有答案。\n'
             '主人翻了个身，没有醒。\n属下把剑放回鞘里，继续等。\n这一夜很长，属下不觉得累。\n只是有些冷。\n'
             '砖缝里漏进月光，细长一条，像是什么东西留下的痕迹，又像什么都不是。\n属下低头看了一眼，没有弯腰。\n'
             '风又来了，檐角的水滴落在院中，声音很轻，却像是落在心上。\n主人今夜睡得早。\n'
             '属下替他掖了一下被角，没有多停。\n退到门外，把门带上，站在廊下继续守。\n就再守一会儿。\n就这样。')

TITLE_JSON = '{"title": "月下守灯", "description": "这一夜，风压低了檐角。"}'


def _mock_urlopen(req, timeout=None):
    """Mock urllib.request.urlopen to intercept all LLM calls."""
    import json as _json
    try:
        body = req.data.decode('utf-8') if req.data else '{}'
        payload = _json.loads(body)
        messages = payload.get('messages', [])
        last = messages[-1]['content'] if messages else ''
        system = messages[0]['content'] if messages else ''
    except Exception:
        last = ''
        system = ''
    if 'JSON' in last or 'title' in last or 'description' in last:
        content = TITLE_JSON
    elif '润色' in system or '润色' in last or '削薄' in system:
        content = LONG_BODY
    else:
        content = LONG_BODY
    resp_body = _json.dumps({'choices': [{'message': {'content': content}}]}).encode('utf-8')
    class FakeResp:
        def read(self):
            return resp_body
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
    return FakeResp()


@pytest.fixture()
def engine_root(tmp_path):
    """Set up a minimal engine root with required JSON fixtures."""
    auto = tmp_path / 'automation'
    auto.mkdir()
    content = tmp_path / 'content'
    content.mkdir()
    draft = tmp_path / 'draft_review'
    draft.mkdir()
    logs = tmp_path / 'logs'
    logs.mkdir()
    output = tmp_path / 'output'
    output.mkdir()

    (auto / 'world_state.json').write_text(json.dumps({
        'meta': {'current_season': '深秋', 'current_watch': '三更', 'weather': '微寒', 'post_count': 0},
        'owner': {'status': '已歇', 'fatigue': 50, 'attention_to_zhen': 30},
        'sister': {'status': 'away', 'pressure': 40, 'renown': 80, 'eta_days': 5},
        'zhen': {'jealousy': 55, 'longing': 70, 'restraint': 65, 'emptiness': 50, 'vigilance': 45, 'guilt': 30},
        'continuity': {'last_summary': '上一夜，灯灭得早。', 'recent_topics': [], 'recent_imagery': [], 'recent_emotions': []},
        'story_arcs': {
            'sister_return': {'enabled': True, 'stage': 0, 'next_trigger_post_count': 99},
            'old_wound': {'enabled': True, 'stage': 0, 'next_trigger_post_count': 99},
            'owner_notice': {'enabled': True, 'stage': 0, 'next_trigger_post_count': 99},
        },
    }), encoding='utf-8')

    (auto / 'manual_overrides.json').write_text(json.dumps({
        'mode': 'draft',
        'forbid_terms': [],
    }), encoding='utf-8')

    (auto / 'topic_rules.json').write_text(json.dumps({
        'categories': [
            {'name': '守夜', 'weight': 3, 'prompts': ['今夜守灯', '廊下等人']},
            {'name': '嫉妒', 'weight': 2, 'prompts': ['姐姐的消息']},
        ],
        'seasonal_boost': {},
        'daily_limit': 3,
    }), encoding='utf-8')

    (auto / 'imagery_pool.json').write_text(json.dumps({
        'visual': ['灯芯', '纸窗', '檐影', '旧漆', '案角', '帐钩', '砚台'],
        'sound': ['更漏', '风压窗纸', '檐角滴水', '火星噼剥', '门轴微哑'],
        'smell': ['墨气', '冷铁味', '灯油气', '夜露气', '潮气'],
        'touch': ['指腹发冷', '袖口微重', '砖面返潮', '指节发紧'],
        'object_groups': {},
    }), encoding='utf-8')

    (auto / 'scene_pool.json').write_text(json.dumps({
        'indoor': ['床榻边缘', '案前', '屏风后'],
        'semi_outdoor': ['廊下', '门槛边'],
        'outer_yard': ['檐角', '院中'],
        'special': ['暗处', '帐外'],
    }), encoding='utf-8')

    (auto / 'emotion_pool.json').write_text(json.dumps({
        'primary': ['贪恋', '幽怨', '克制', '嫉妒', '不服', '空寂'],
        'secondary': ['羞', '惭', '倦', '慌', '失落', '警觉', '旧伤翻起', '麻木'],
        'pairing_hints': {
            '嫉妒': ['失落', '不服', '羞'],
            '贪恋': ['克制', '慌'],
            '空寂': ['倦', '麻木'],
            '不服': ['旧伤翻起', '警觉'],
        },
    }), encoding='utf-8')

    (auto / 'recent_memories.json').write_text(json.dumps([
        {'id': 'mem1', 'summary': '廊下起了风，主人的灯灭得很早。', 'emotion': '克制'},
    ]), encoding='utf-8')

    (auto / 'future_fragments.json').write_text(json.dumps([]), encoding='utf-8')
    (auto / 'memory_anchors.json').write_text(json.dumps([
        {'id': 'anc1', 'summary': '那年冬天，主人第一次叫了全真的名字。', 'emotion': ['贪恋', '克制'], 'trigger_tags': ['守夜', '嫉妒'], 'weight': 2},
    ]), encoding='utf-8')

    (auto / 'night_journal_stats.json').write_text(json.dumps({
        'post_count': 0, 'successful_posts': 0, 'failed_runs': 0,
        'repaired_posts': 0, 'topics': {}, 'scenes': {},
        'last_quality_failures': [],
    }), encoding='utf-8')

    (auto / 'event_map_rules.json').write_text(json.dumps({}), encoding='utf-8')

    os.environ['ENGINE_ROOT'] = str(tmp_path)
    os.environ['BLOG_OUTPUT_DIR'] = str(output)
    os.environ['LOG_DIR'] = str(logs)
    os.environ['OPENAI_API_KEY'] = 'test-key'
    os.environ['OPENAI_BASE_URL'] = 'https://fake.api/v1'
    os.environ['OPENAI_MODEL'] = 'gpt-test'

    yield tmp_path

    for k in ['ENGINE_ROOT', 'BLOG_OUTPUT_DIR', 'LOG_DIR', 'OPENAI_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_MODEL']:
        os.environ.pop(k, None)


def test_run_produces_output_file(engine_root):
    import importlib
    import night_journal.application as app_mod
    importlib.reload(app_mod)

    with mock.patch('urllib.request.urlopen', side_effect=_mock_urlopen):
        result = app_mod.run(engine_root)

    assert result.ok is True
    assert result.stage == 'complete'
    out_file = Path(result.message)
    assert out_file.exists()
    content = out_file.read_text(encoding='utf-8')
    assert 'title:' in content
    assert '全真' in content


def test_run_result_has_expected_fields(engine_root):
    import importlib
    import night_journal.application as app_mod
    importlib.reload(app_mod)

    with mock.patch('urllib.request.urlopen', side_effect=_mock_urlopen):
        result = app_mod.run(engine_root)

    assert 'title' in result.data
    assert 'slug' in result.data
    assert 'mode' in result.data
    assert 'category' in result.data


def test_run_updates_world_state(engine_root):
    import importlib
    import night_journal.application as app_mod
    importlib.reload(app_mod)

    with mock.patch('urllib.request.urlopen', side_effect=_mock_urlopen):
        app_mod.run(engine_root)

    state = json.loads((engine_root / 'automation' / 'world_state.json').read_text())
    assert state['meta']['post_count'] == 1
    assert state['continuity']['last_summary'] != ''


def test_run_updates_stats(engine_root):
    import importlib
    import night_journal.application as app_mod
    importlib.reload(app_mod)

    with mock.patch('urllib.request.urlopen', side_effect=_mock_urlopen):
        app_mod.run(engine_root)

    stats = json.loads((engine_root / 'automation' / 'night_journal_stats.json').read_text())
    assert stats['post_count'] == 1
    assert stats['successful_posts'] == 1
