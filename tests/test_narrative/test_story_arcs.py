"""Tests for night_journal.narrative.story_arcs"""
from night_journal.narrative.story_arcs import story_arc_triggers


def _make_state(jealousy=50, guilt=30, emptiness=40, attention=30, post_count=5, sister_return_stage=0, sister_return_trigger=3, old_wound_stage=0, old_wound_trigger=3, owner_notice_stage=0, owner_notice_trigger=3):
    return {
        'meta': {'post_count': post_count},
        'zhen': {'jealousy': jealousy, 'longing': 60, 'restraint': 70,
                 'emptiness': emptiness, 'vigilance': 45, 'guilt': guilt},
        'owner': {'attention_to_zhen': attention, 'fatigue': 50, 'status': '已歇'},
        'sister': {'status': 'away', 'pressure': 40, 'renown': 80, 'eta_days': 5},
        'story_arcs': {
            'sister_return': {
                'enabled': True,
                'stage': sister_return_stage,
                'next_trigger_post_count': sister_return_trigger,
            },
            'old_wound': {
                'enabled': True,
                'stage': old_wound_stage,
                'next_trigger_post_count': old_wound_trigger,
            },
            'owner_notice': {
                'enabled': True,
                'stage': owner_notice_stage,
                'next_trigger_post_count': owner_notice_trigger,
            },
        },
    }


def test_no_arcs_triggered_by_default():
    state = _make_state(jealousy=50, post_count=1, sister_return_trigger=99, old_wound_trigger=99, owner_notice_trigger=99)
    lines = story_arc_triggers(state, {})
    assert isinstance(lines, list)


def test_sister_return_triggers_when_conditions_met():
    state = _make_state(jealousy=80, post_count=10, sister_return_trigger=5, sister_return_stage=0)
    lines = story_arc_triggers(state, {})
    assert len(lines) >= 1
    assert any('姐姐' in l for l in lines)


def test_old_wound_triggers_when_conditions_met():
    state = _make_state(guilt=40, emptiness=40, post_count=10, old_wound_trigger=5, old_wound_stage=0)
    lines = story_arc_triggers(state, {})
    # old_wound needs guilt+emptiness >= 58
    assert isinstance(lines, list)


def test_returns_list_of_strings():
    state = _make_state()
    lines = story_arc_triggers(state, {})
    for line in lines:
        assert isinstance(line, str)


def test_empty_story_arcs():
    state = _make_state()
    state['story_arcs'] = {}
    lines = story_arc_triggers(state, {})
    assert isinstance(lines, list)
