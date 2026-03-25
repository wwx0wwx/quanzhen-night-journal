"""Tests for night_journal.quality.checker"""
import pytest
from pathlib import Path
from night_journal.quality.checker import quality_check, guard_publish


OVERRIDES = {'forbid_terms': []}


def _make_paths_fn(paths):
    return lambda n: paths[:n]


LONG_BODY = '廊下起了风。' * 40  # 220+ chars


# --- quality_check tests ---

def test_pass_on_good_content(tmp_path):
    reasons = quality_check(LONG_BODY, '月下守灯', '这一夜灯将尽。', OVERRIDES, _make_paths_fn([]))
    assert reasons == []


def test_fail_on_short_body():
    reasons = quality_check('太短', '月下守灯', '这一夜灯将尽。', OVERRIDES, _make_paths_fn([]))
    assert '正文过短' in reasons


def test_fail_on_banned_term():
    reasons = quality_check(LONG_BODY + '我嫉妒', '月下守灯', '这一夜灯将尽。', OVERRIDES, _make_paths_fn([]))
    assert any('命中禁词' in r for r in reasons)


def test_fail_on_custom_forbid_term():
    overrides = {'forbid_terms': ['禁词测试']}
    reasons = quality_check(LONG_BODY + '禁词测试', '月下守灯', '这一夜灯将尽。', overrides, _make_paths_fn([]))
    assert any('禁词测试' in r for r in reasons)


def test_fail_on_title_template():
    reasons = quality_check(LONG_BODY, '夜札：月下', '这一夜灯将尽。', OVERRIDES, _make_paths_fn([]))
    assert '标题模板化' in reasons


def test_fail_on_description_tech_tone():
    reasons = quality_check(LONG_BODY, '月下守灯', '由全真夜札引擎生成的内容。', OVERRIDES, _make_paths_fn([]))
    assert 'description 技术味过重' in reasons


def test_overlap_check_with_recent_posts(tmp_path):
    # Create a recent post with overlapping tokens
    recent = tmp_path / 'recent.md'
    recent.write_text('廊下纸窗擦剑袖中主人睡得砖缝残茶灯芯帐外', encoding='utf-8')
    body_with_overlap = LONG_BODY + '廊下纸窗擦剑袖中主人睡得砖缝残茶灯芯帐外'
    reasons = quality_check(body_with_overlap, '月下守灯', '这一夜灯将尽。', OVERRIDES, _make_paths_fn([recent]))
    assert '与近三篇重复度过高' in reasons


def test_overlap_check_no_crash_on_missing_files():
    missing = Path('/nonexistent/path.md')
    reasons = quality_check(LONG_BODY, '月下守灯', '这一夜灯将尽。', OVERRIDES, _make_paths_fn([missing]))
    # Should not crash, overlap check silently skipped
    assert isinstance(reasons, list)


# --- guard_publish tests ---

def test_guard_allows_normal():
    state = {'meta': {'last_publish_day_utc': '2026-01-01'}, 'scheduler': {'max_posts_per_day': 1}}
    # Should not raise
    guard_publish({}, state, '2026-03-25')


def test_guard_blocks_pause():
    with pytest.raises(RuntimeError, match='paused'):
        guard_publish({'pause_publishing': True}, {}, '2026-03-25')


def test_guard_blocks_manual_only():
    with pytest.raises(RuntimeError, match='manual-only'):
        guard_publish({'mode': 'manual-only'}, {}, '2026-03-25')


def test_guard_blocks_daily_limit():
    state = {'meta': {'last_publish_day_utc': '2026-03-25'}, 'scheduler': {'max_posts_per_day': 1}}
    with pytest.raises(RuntimeError, match='Daily publish limit'):
        guard_publish({}, state, '2026-03-25')


def test_guard_allows_new_day():
    state = {'meta': {'last_publish_day_utc': '2026-03-24'}, 'scheduler': {'max_posts_per_day': 1}}
    guard_publish({}, state, '2026-03-25')  # Should not raise


def test_guard_allows_zero_limit():
    state = {'meta': {'last_publish_day_utc': '2026-03-25'}, 'scheduler': {'max_posts_per_day': 0}}
    guard_publish({}, state, '2026-03-25')  # 0 means no limit, should not raise
