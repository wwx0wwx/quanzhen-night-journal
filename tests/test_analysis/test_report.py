"""Tests for night_journal.analysis.report"""
import json
from pathlib import Path
from night_journal.analysis.report import (
    title_shape,
    latest_post_files,
    analyze,
    print_report,
)


# --- title_shape ---

def test_title_shape_time():
    assert title_shape('今夜无人') == '时间切片'

def test_title_shape_half_thought():
    assert title_shape('不宜近前') == '半句心迹'

def test_title_shape_action():
    assert title_shape('替主人挡风') == '动作残片'

def test_title_shape_default():
    assert title_shape('月下白梅') == '极简意象'


# --- latest_post_files ---

def test_latest_post_files_returns_limit(tmp_path):
    content = tmp_path / 'content'
    draft = tmp_path / 'draft'
    content.mkdir()
    draft.mkdir()
    for i in range(5):
        (content / f'post-{i:02d}.md').write_text(f'body {i}', encoding='utf-8')
    files = latest_post_files(content, draft, limit=3)
    assert len(files) == 3

def test_latest_post_files_combines_dirs(tmp_path):
    content = tmp_path / 'content'
    draft = tmp_path / 'draft'
    content.mkdir()
    draft.mkdir()
    (content / 'a.md').write_text('a', encoding='utf-8')
    (draft / 'b.md').write_text('b', encoding='utf-8')
    files = latest_post_files(content, draft, limit=10)
    assert len(files) == 2

def test_latest_post_files_empty(tmp_path):
    content = tmp_path / 'content'
    draft = tmp_path / 'draft'
    content.mkdir()
    draft.mkdir()
    files = latest_post_files(content, draft)
    assert files == []


# --- analyze ---

STATE = {
    'meta': {'post_count': 10},
    'owner': {'fatigue': 50, 'attention_to_zhen': 30},
    'sister': {'pressure': 40, 'renown': 80},
    'zhen': {'jealousy': 55, 'longing': 70, 'restraint': 65, 'emptiness': 50},
    'continuity': {'recent_scenes': ['廊下', '廊下']},
    'story_arcs': {
        'sister_return': {'stage': 0, 'enabled': True, 'next_trigger_post_count': 99},
    },
}

STATS = {
    'post_count': 10,
    'successful_posts': 9,
    'failed_runs': 1,
    'repaired_runs': 2,
    'topics': {'守夜': 5, '嫉妒': 3},
    'scenes': {'廊下': 4},
    'primary_emotions': {'克制': 6},
    'secondary_emotions': {'失落': 4},
    'imagery': {'灯': 8, '剑': 5},
    'last_quality_failures': ['正文过短'],
}

MEMORIES = [
    {'at': '2026-01-01', 'title': '守灯', 'summary': '廊下起风'},
]


def test_analyze_returns_dict(tmp_path):
    content = tmp_path / 'content'
    draft = tmp_path / 'draft'
    content.mkdir()
    draft.mkdir()
    report = analyze(STATE, STATS, MEMORIES, content, draft)
    assert isinstance(report, dict)


def test_analyze_summary_fields(tmp_path):
    content = tmp_path / 'content'
    draft = tmp_path / 'draft'
    content.mkdir()
    draft.mkdir()
    report = analyze(STATE, STATS, MEMORIES, content, draft)
    assert report['summary']['post_count'] == 10
    assert report['summary']['successful_posts'] == 9


def test_analyze_world_state_fields(tmp_path):
    content = tmp_path / 'content'
    draft = tmp_path / 'draft'
    content.mkdir()
    draft.mkdir()
    report = analyze(STATE, STATS, MEMORIES, content, draft)
    assert report['world_state']['owner_fatigue'] == 50
    assert report['world_state']['zhen_jealousy'] == 55


def test_analyze_with_posts(tmp_path):
    content = tmp_path / 'content'
    draft = tmp_path / 'draft'
    content.mkdir()
    draft.mkdir()
    md = '---\ntitle: "月下守灯"\ndescription: "这一夜。"\n---\n\n廊下起了风，灯摇了一夜。'
    (content / '20260325-night-note.md').write_text(md, encoding='utf-8')
    report = analyze(STATE, STATS, MEMORIES, content, draft)
    assert '月下守灯' in report['titles']
    assert report['word_counts']['count'] == 1


def test_analyze_quality_failures(tmp_path):
    content = tmp_path / 'content'
    draft = tmp_path / 'draft'
    content.mkdir()
    draft.mkdir()
    report = analyze(STATE, STATS, MEMORIES, content, draft)
    assert '正文过短' in report['last_quality_failures']


def test_analyze_suggestions_present(tmp_path):
    content = tmp_path / 'content'
    draft = tmp_path / 'draft'
    content.mkdir()
    draft.mkdir()
    report = analyze(STATE, STATS, MEMORIES, content, draft)
    assert len(report['suggestions']) > 0


def test_print_report_no_crash(tmp_path, capsys):
    content = tmp_path / 'content'
    draft = tmp_path / 'draft'
    content.mkdir()
    draft.mkdir()
    report = analyze(STATE, STATS, MEMORIES, content, draft)
    print_report(report)  # Should not raise
    captured = capsys.readouterr()
    assert '全真夜札' in captured.out
