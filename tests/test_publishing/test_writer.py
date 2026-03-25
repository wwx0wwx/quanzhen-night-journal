"""Tests for night_journal.publishing.writer"""
from datetime import datetime, timezone
from pathlib import Path
from night_journal.publishing.writer import build_markdown, route_output_dir, write_post

UTC = timezone.utc
NOW = datetime(2026, 3, 25, 22, 0, 0, tzinfo=UTC)


def test_build_markdown_contains_title():
    md, _, _ = build_markdown('月下守灯', '这一夜灯将尽。', '守夜', '正文内容', NOW)
    assert 'title: "月下守灯"' in md


def test_build_markdown_contains_description():
    md, _, _ = build_markdown('月下守灯', '这一夜灯将尽。', '守夜', '正文内容', NOW)
    assert 'description: "这一夜灯将尽。"' in md


def test_build_markdown_contains_body():
    md, _, _ = build_markdown('月下守灯', '这一夜灯将尽。', '守夜', '正文内容', NOW)
    assert '正文内容' in md


def test_build_markdown_contains_tags():
    md, _, _ = build_markdown('月下守灯', '这一夜灯将尽。', '守夜', '正文内容', NOW)
    assert '全真' in md
    assert '夜札' in md
    assert '守夜' in md


def test_build_markdown_slug_format():
    _, _, slug = build_markdown('月下守灯', '这一夜灯将尽。', '守夜', '正文内容', NOW)
    assert slug.endswith('-night-note')
    assert '20260325' in slug


def test_build_markdown_now_str_format():
    _, now_str, _ = build_markdown('月下守灯', '这一夜灯将尽。', '守夜', '正文内容', NOW)
    assert 'Z' in now_str or '+' in now_str


def test_route_output_dir_auto(tmp_path):
    content = tmp_path / 'content'
    draft = tmp_path / 'draft'
    result = route_output_dir({'mode': 'auto'}, content, draft)
    assert result == content


def test_route_output_dir_review_first(tmp_path):
    content = tmp_path / 'content'
    draft = tmp_path / 'draft'
    result = route_output_dir({'mode': 'review-first'}, content, draft)
    assert result == draft


def test_route_output_dir_default_to_draft(tmp_path):
    content = tmp_path / 'content'
    draft = tmp_path / 'draft'
    result = route_output_dir({}, content, draft)
    # no mode key → defaults to 'auto' → content
    assert result == content


def test_write_post_creates_file(tmp_path):
    content = tmp_path / 'content'
    draft = tmp_path / 'draft'
    content.mkdir()
    draft.mkdir()
    path, now_str, slug = write_post(
        title='月下守灯',
        description='这一夜灯将尽。',
        category='守夜',
        body='廊下起了风。' * 40,
        overrides={'mode': 'auto'},
        content_dir=content,
        draft_review_dir=draft,
        now=NOW,
    )
    assert path.exists()
    assert path.parent == content
    text = path.read_text(encoding='utf-8')
    assert '月下守灯' in text


def test_write_post_draft_mode(tmp_path):
    content = tmp_path / 'content'
    draft = tmp_path / 'draft'
    content.mkdir()
    draft.mkdir()
    path, _, _ = write_post(
        title='月下守灯',
        description='这一夜灯将尽。',
        category='守夜',
        body='廊下起了风。' * 40,
        overrides={'mode': 'draft'},
        content_dir=content,
        draft_review_dir=draft,
        now=NOW,
    )
    assert path.parent == draft
