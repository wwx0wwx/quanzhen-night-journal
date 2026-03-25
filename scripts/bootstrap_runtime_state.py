#!/usr/bin/env python3
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
AUTO = BASE / 'automation'
TARGETS = [
    ('world_state.example.json', 'world_state.json'),
    ('recent_memories.example.json', 'recent_memories.json'),
    ('night_journal_stats.example.json', 'night_journal_stats.json'),
    ('manual_overrides.example.json', 'manual_overrides.json'),
    ('memory_anchors.example.json', 'memory_anchors.json'),
    ('future_fragments.example.json', 'future_fragments.json'),
    ('topic_rules.example.json', 'topic_rules.json'),
]

for src_name, dst_name in TARGETS:
    src = AUTO / src_name
    dst = AUTO / dst_name
    if not src.exists():
        print(f'SKIP missing template: {src_name}')
        continue
    if dst.exists():
        print(f'SKIP exists: {dst_name}')
        continue
    dst.write_text(src.read_text(encoding='utf-8'), encoding='utf-8')
    print(f'CREATED {dst_name}')

(base:=BASE / 'draft_review').mkdir(parents=True, exist_ok=True)
(base:=BASE / 'logs').mkdir(parents=True, exist_ok=True)
print('Runtime bootstrap complete.')
