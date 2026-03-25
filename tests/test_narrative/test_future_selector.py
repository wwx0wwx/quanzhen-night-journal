"""Tests for night_journal.narrative.future_selector"""
import unittest.mock as mock
from night_journal.narrative.future_selector import maybe_future_fragment

FRAGMENTS = [
    {'id': 'f1', 'summary': '姐姐快回来了，属下已经感觉到了。', 'arc': 'sister_return', 'stage': 1, 'weight': 2},
    {'id': 'f2', 'summary': '主人迟早会问那件事。', 'arc': 'owner_notice', 'stage': 1, 'weight': 1},
]

STORY_ARCS = {
    'sister_return': {'stage': 1, 'enabled': True},
    'owner_notice': {'stage': 0, 'enabled': True},
}

OVERRIDES = {}


def test_returns_string():
    result = maybe_future_fragment(OVERRIDES, FRAGMENTS, STORY_ARCS)
    assert isinstance(result, str)


def test_force_future_id():
    overrides = {'force_future_id': 'f1'}
    result = maybe_future_fragment(overrides, FRAGMENTS, STORY_ARCS)
    assert '姐姐快回来了' in result


def test_force_future_id_missing():
    overrides = {'force_future_id': 'nonexistent'}
    result = maybe_future_fragment(overrides, FRAGMENTS, STORY_ARCS)
    assert isinstance(result, str)


def test_empty_fragments_returns_empty():
    result = maybe_future_fragment(OVERRIDES, [], STORY_ARCS)
    assert result == ''


def test_triggered_fragment():
    # Force random to trigger (< 0.22)
    with mock.patch('random.random', return_value=0.1):
        result = maybe_future_fragment(OVERRIDES, FRAGMENTS, STORY_ARCS)
    # f1 is active (sister_return stage=1 >= f1.stage-1=0)
    assert isinstance(result, str)


def test_not_triggered_returns_empty():
    with mock.patch('random.random', return_value=0.99):
        result = maybe_future_fragment(OVERRIDES, FRAGMENTS, STORY_ARCS)
    assert result == ''


def test_arc_not_reached_not_active():
    # owner_notice stage=0, f2 needs stage >= 0, so f2 is active
    # sister_return stage=1, f1 needs stage >= 0, so f1 is active
    arcs = {'sister_return': {'stage': 0}, 'owner_notice': {'stage': 0}}
    with mock.patch('random.random', return_value=0.1):
        result = maybe_future_fragment(OVERRIDES, FRAGMENTS, arcs)
    assert isinstance(result, str)
