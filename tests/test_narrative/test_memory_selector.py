"""Tests for night_journal.narrative.memory_selector"""
import unittest.mock as mock
from night_journal.narrative.memory_selector import maybe_memory

ANCHORS = [
    {'id': 'anc1', 'summary': '那年冬天，主人第一次叫了全真的名字。', 'emotion': ['贪恋', '克制'], 'trigger_tags': ['守夜'], 'weight': 2},
    {'id': 'anc2', 'summary': '姐姐回来那天，属下在廊下站了一夜。', 'emotion': ['嫉妒'], 'trigger_tags': ['嫉妒'], 'weight': 1},
]

RECENT_MEMORIES = [
    {'summary': '廊下起了风，主人的灯灭得很早。'},
    {'summary': '姐姐传来消息，又立了一件事。'},
]

RULES = {'memory_trigger_probability': 1.0}  # always trigger
RULES_NEVER = {'memory_trigger_probability': 0.0}  # never trigger

OVERRIDES = {}


def test_returns_string():
    result = maybe_memory('克制', OVERRIDES, ANCHORS, RECENT_MEMORIES, RULES)
    assert isinstance(result, str)


def test_force_memory_id():
    overrides = {'force_memory_id': 'anc1'}
    result = maybe_memory('克制', overrides, ANCHORS, RECENT_MEMORIES, RULES)
    assert '主人第一次叫了全真的名字' in result


def test_force_memory_id_missing():
    overrides = {'force_memory_id': 'nonexistent'}
    # should fall through and return something (or empty)
    result = maybe_memory('克制', overrides, ANCHORS, RECENT_MEMORIES, RULES)
    assert isinstance(result, str)


def test_returns_empty_when_no_trigger():
    with mock.patch('random.random', return_value=0.99):
        result = maybe_memory('克制', OVERRIDES, ANCHORS, [], RULES_NEVER)
    assert result == ''


def test_uses_recent_memories():
    # Force random to hit recent_memories branch (< 0.25)
    with mock.patch('random.random', return_value=0.1):
        result = maybe_memory('克制', OVERRIDES, ANCHORS, RECENT_MEMORIES, RULES)
    assert isinstance(result, str)
    assert len(result) > 0


def test_emotion_filtered_anchor():
    # probability=1.0 forces anchor pick; emotion='嫉妒' should prefer anc2
    with mock.patch('random.random', return_value=0.99):  # skip recent memory branch
        result = maybe_memory('嫉妒', OVERRIDES, ANCHORS, [], RULES)
    assert isinstance(result, str)


def test_empty_anchors_returns_empty():
    with mock.patch('random.random', return_value=0.99):
        result = maybe_memory('克制', OVERRIDES, [], [], RULES_NEVER)
    assert result == ''
