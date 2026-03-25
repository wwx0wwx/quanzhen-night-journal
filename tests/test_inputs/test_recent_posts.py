"""Tests for night_journal.inputs.recent_posts"""
import pytest
from pathlib import Path
from night_journal.inputs.recent_posts import (
    strip_front_matter,
    parse_front_matter,
    extract_repeated_phrases,
)


SAMPLE_MD = '''---
title: "月下无眠"
date: 2026-01-01T00:00:00Z
description: "灯将尽时留下的。"
---

廊下起了风，灯摇了一夜。剑还在原处。
'''


def test_strip_front_matter_removes_yaml():
    body = strip_front_matter(SAMPLE_MD)
    assert '廊下起了风' in body
    assert 'title:' not in body
    assert '---' not in body


def test_strip_front_matter_no_yaml():
    plain = '今夜无事，只是等。'
    assert strip_front_matter(plain) == plain


def test_parse_front_matter_extracts_title():
    fm = parse_front_matter(SAMPLE_MD)
    assert fm.get('title') == '月下无眠'


def test_parse_front_matter_extracts_description():
    fm = parse_front_matter(SAMPLE_MD)
    assert '灯将尽' in fm.get('description', '')


def test_parse_front_matter_no_yaml():
    fm = parse_front_matter('无 front matter 的正文')
    assert fm == {}


def test_extract_repeated_phrases_finds_repeats():
    texts = ['廊下起风，灯摇。', '廊下又起风，灯又摇。']
    phrases = extract_repeated_phrases(texts)
    assert '廊下' in phrases or '灯' in phrases


def test_extract_repeated_phrases_empty():
    phrases = extract_repeated_phrases([])
    assert isinstance(phrases, list)


def test_extract_repeated_phrases_limit():
    texts = ['廊下灯剑茶纸窗砖缝擦了袖中指节更冷天色'] * 3
    phrases = extract_repeated_phrases(texts)
    assert len(phrases) <= 16
