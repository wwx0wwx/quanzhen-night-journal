"""Tests for night_journal.generation.prompt_builder"""
import pytest


STATE = {
    'meta': {
        'current_season': '深秋',
        'current_watch': '三更',
        'weather': '微寒',
        'post_count': 10,
    },
    'owner': {'status': '已歇', 'fatigue': 60, 'attention_to_zhen': 30},
    'sister': {'status': '在外', 'pressure': 40, 'renown': 80},
    'zhen': {
        'jealousy': 55, 'longing': 70, 'restraint': 65,
        'emptiness': 50, 'vigilance': 45, 'guilt': 30,
    },
    'continuity': {'last_summary': '上一夜，主人问了属下一句话，属下没有答。'},
}

OVERRIDES = {'forbid_terms': ['测试禁词']}
RULES = {'target_word_count': 380}
RECENT_MEMORIES = [
    {'summary': '廊下起了风，主人的灯灭得很早。'},
    {'summary': '姐姐传来消息，说又立了一件事。'},
]


def make_prompt(**kwargs):
    from night_journal.generation.prompt_builder import build_prompt
    defaults = dict(
        state=STATE,
        overrides=OVERRIDES,
        rules=RULES,
        recent_memories=RECENT_MEMORIES,
        events=['今夜风大，廊下的灯摇了一夜。'],
        topic='守夜',
        memory_block='',
        future_block='',
        repeated_phrases=['灯', '剑'],
        chosen_imagery=['月', '霜'],
        chosen_scene='床榻边缘',
        primary='克制',
        secondary='幽怨',
        arc_lines=['旧伤未愈，又起新事。'],
    )
    defaults.update(kwargs)
    return build_prompt(**defaults)


def test_prompt_contains_owner():
    prompt = make_prompt()
    assert '主人' in prompt


def test_prompt_contains_season():
    prompt = make_prompt()
    assert '深秋' in prompt


def test_prompt_contains_topic():
    prompt = make_prompt()
    assert '守夜' in prompt


def test_prompt_contains_arc():
    prompt = make_prompt()
    assert '旧伤未愈' in prompt


def test_prompt_contains_forbid_term():
    prompt = make_prompt()
    assert '测试禁词' in prompt


def test_prompt_contains_repeated_risk():
    prompt = make_prompt()
    assert '灯' in prompt


def test_prompt_nonempty_with_empty_memories():
    prompt = make_prompt(recent_memories=[])
    assert len(prompt) > 100


def test_prompt_nonempty_with_empty_arc():
    prompt = make_prompt(arc_lines=[])
    assert '今夜没有新的命数' in prompt


def test_prompt_nonempty_with_empty_repeated():
    prompt = make_prompt(repeated_phrases=[])
    assert '无明显重复' in prompt


def test_prompt_word_count_hint():
    prompt = make_prompt()
    assert '380' in prompt
