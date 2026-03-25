#!/usr/bin/env python3
"""Night journal analysis entry point.

Delegates to night_journal.analysis when the package is available,
falls back to inline logic for backward compatibility.
"""
import json
import os
import sys
from pathlib import Path

BASE = Path(os.environ.get('ENGINE_ROOT', '/opt/blog-src'))
AUTO = BASE / 'automation'
CONTENT = BASE / 'content' / 'posts'
DRAFT = BASE / 'draft_review'

# --- Try package-based analysis ---
try:
    sys.path.insert(0, str(BASE))
    from night_journal.analysis import analyze, print_report
    from night_journal.config import load_settings

    settings = load_settings(BASE)
    state = json.loads((AUTO / 'world_state.json').read_text())
    stats = json.loads((AUTO / 'night_journal_stats.json').read_text())
    recent_memories = json.loads((AUTO / 'recent_memories.json').read_text())

    report = analyze(
        state=state,
        stats=stats,
        recent_memories=recent_memories,
        content_dir=settings.content_dir,
        draft_dir=settings.draft_review_dir,
    )
    print_report(report)
    sys.exit(0)

except Exception as e:
    print(f'[analyze_journal] package mode failed ({e}), falling back to inline mode', file=sys.stderr)

# --- Fallback: inline legacy logic ---
from collections import Counter

def strip_front_matter(text):
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text.strip()

def parse_front_matter(text):
    data = {}
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                if ':' in line:
                    k, v = line.split(':', 1)
                    data[k.strip()] = v.strip().strip('"')
    return data

state = json.loads((AUTO / 'world_state.json').read_text())
stats = json.loads((AUTO / 'night_journal_stats.json').read_text())
recent_memories = json.loads((AUTO / 'recent_memories.json').read_text())

files = sorted(list(CONTENT.glob('*.md')) + list(DRAFT.glob('*.md')), key=lambda p: p.stat().st_mtime, reverse=True)[:12]
word_counts, term_risk, titles, descriptions = [], Counter(), [], []
for p in files:
    raw = p.read_text(encoding='utf-8')
    fm = parse_front_matter(raw)
    body = strip_front_matter(raw)
    word_counts.append(len(body))
    titles.append(fm.get('title', ''))
    descriptions.append(fm.get('description', ''))
    for t in ['廊下', '纸窗', '灯', '剑', '茶', '案上', '袖中', '砖缝', '帐外', '薄衾', '铜盆']:
        if t in body:
            term_risk[t] += 1

print('== 全真夜札系统复盘 (legacy) ==')
print(f"总发文数: {stats.get('post_count', 0)}  成功: {stats.get('successful_posts', 0)}  失败: {stats.get('failed_runs', 0)}")
print()
print('== 最近标题 ==')
for t in titles[:8]:
    print('-', t)
if word_counts:
    print(f"\n== 字数概况 ==  平均:{sum(word_counts)//len(word_counts)}  最长:{max(word_counts)}  最短:{min(word_counts)}")
print('\n== 最近质量失败原因 ==')
for r in stats.get('last_quality_failures', [])[-10:]:
    print('-', r)
