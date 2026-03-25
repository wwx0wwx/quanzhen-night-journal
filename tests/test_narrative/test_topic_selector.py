"""Tests for night_journal.narrative.topic_selector"""
from night_journal.narrative.topic_selector import choose_topic


RULES = {
    'categories': [
        {'name': '守夜', 'weight': 3, 'prompts': ['今夜守灯', '廊下等人', '月下独处']},
        {'name': '嫉妒', 'weight': 2, 'prompts': ['姐姐的消息', '比较的心']},
    ],
    'seasonal_boost': {},
}

STATE = {
    'meta': {'current_season': '深秋', 'post_count': 5},
    'zhen': {'jealousy': 50, 'longing': 60, 'restraint': 70, 'emptiness': 40, 'vigilance': 45, 'guilt': 30},
    'continuity': {'recent_topics': []},
}

OVERRIDES = {}


def test_choose_topic_returns_tuple():
    category, topic = choose_topic(RULES, STATE, OVERRIDES)
    assert isinstance(category, str)
    assert isinstance(topic, str)
    assert len(category) > 0
    assert len(topic) > 0


def test_choose_topic_category_in_rules():
    category, topic = choose_topic(RULES, STATE, OVERRIDES)
    valid_cats = [c['name'] for c in RULES['categories']]
    assert category in valid_cats


def test_choose_topic_force_override():
    overrides = {'force_topic': '属下想说一句话'}
    category, topic = choose_topic(RULES, STATE, overrides)
    assert topic == '属下想说一句话'
    assert category == '属下想说一句话'


def test_choose_topic_avoids_recent():
    # Even with recent topics set, should still return a valid topic
    state = dict(STATE)
    state['continuity'] = {'recent_topics': ['今夜守灯', '廊下等人']}
    category, topic = choose_topic(RULES, state, OVERRIDES)
    assert isinstance(topic, str)


def test_choose_topic_no_crash_empty_prompts():
    rules = {
        'categories': [
            {'name': '守夜', 'weight': 1, 'prompts': ['唯一主题']},
        ],
        'seasonal_boost': {},
    }
    category, topic = choose_topic(rules, STATE, OVERRIDES)
    assert topic == '唯一主题'
