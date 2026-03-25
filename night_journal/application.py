from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

from .config import load_settings
from .logging_utils import get_logger
from .models import RunResult
from .inputs.state_store import StateStore
from .inputs.content_catalog import ContentCatalog
from .inputs.vps_signals import collect_vps_signals
from .inputs.recent_posts import build_recent_context
from .narrative.topic_selector import choose_topic
from .narrative.material_selector import choose_world_material
from .narrative.memory_selector import maybe_memory
from .narrative.future_selector import maybe_future_fragment
from .narrative.story_arcs import story_arc_triggers
from .generation import (
    api_chat,
    build_prompt,
    refine_body,
    generate_title_and_description,
)

UTC = timezone.utc


def _quality_check(body: str, title: str, description: str, overrides: dict, recent_post_paths_fn) -> list[str]:
    """Return list of quality failure reasons (empty = pass)."""
    import re
    reasons = []
    if len(body.strip()) < 220:
        reasons.append('正文过短')
    banned = ['由全真夜札引擎生成', '我嫉妒', '我好恨', '我爱主人', '今夜共有'] + overrides.get('forbid_terms', [])
    for b in banned:
        if b and (b in body or b in title or b in description):
            reasons.append(f'命中禁词:{b}')
    if title.startswith('夜札：'):
        reasons.append('标题模板化')
    if '由' in description and '引擎' in description:
        reasons.append('description 技术味过重')
    overlap = 0
    try:
        paths = recent_post_paths_fn(3)
        merged_recent = '\n'.join(
            p.read_text(encoding='utf-8')[:700] for p in paths
        )
        for token in ['廊下', '纸窗', '擦剑', '袖中', '主人睡得', '砖缝', '残茶', '灯芯', '帐外']:
            if token in body and token in merged_recent:
                overlap += 1
        if overlap >= 4:
            reasons.append('与近三篇重复度过高')
    except Exception:
        pass
    return reasons


def _update_story_arcs(state: dict) -> None:
    pc = state['meta']['post_count']
    arcs = state.get('story_arcs', {})
    if not arcs:
        return
    ow = arcs.get('old_wound', {})
    if ow.get('enabled') and pc >= ow.get('next_trigger_post_count', 9999) and ow.get('stage') == 0 and state['zhen']['guilt'] + state['zhen']['emptiness'] >= 58:
        arcs['old_wound']['stage'] = 1
        arcs['old_wound']['next_trigger_post_count'] = pc + 7
    sr = arcs.get('sister_return', {})
    if sr.get('enabled') and pc >= sr.get('next_trigger_post_count', 9999) and state['zhen']['jealousy'] >= 74:
        arcs['sister_return']['stage'] = min(2, sr.get('stage', 0) + 1)
        arcs['sister_return']['next_trigger_post_count'] = pc + 6
        state['sister']['pressure'] = min(100, state['sister']['pressure'] + 6)
    on = arcs.get('owner_notice', {})
    if on.get('enabled') and pc >= on.get('next_trigger_post_count', 9999) and state['owner']['attention_to_zhen'] >= 42:
        arcs['owner_notice']['stage'] = min(2, on.get('stage', 0) + 1)
        arcs['owner_notice']['next_trigger_post_count'] = pc + 8
        state['owner']['attention_to_zhen'] = min(100, state['owner']['attention_to_zhen'] + 4)


def _drift_state(state: dict) -> None:
    """Apply random emotional drift to world state."""
    z = state['zhen']
    z['jealousy'] = min(100, max(0, z['jealousy'] + random.choice([-1, 0, 1, 2, 3])))
    z['longing'] = min(100, max(0, z['longing'] + random.choice([-1, 0, 1, 2])))
    z['restraint'] = min(100, max(0, z['restraint'] + random.choice([-2, -1, 0, 1])))
    z['emptiness'] = min(100, max(0, z['emptiness'] + random.choice([-2, -1, 0, 1, 2])))
    z['vigilance'] = min(100, max(0, z['vigilance'] + random.choice([-1, 0, 1, 2])))
    z['guilt'] = min(100, max(0, z['guilt'] + random.choice([-2, -1, 0, 1])))
    state['owner']['fatigue'] = min(100, max(0, state['owner']['fatigue'] + random.choice([-3, -1, 0, 1, 2])))
    if state['sister']['status'] == 'away' and state['sister'].get('eta_days', 0) > 0:
        state['sister']['eta_days'] -= 1
        state['sister']['pressure'] = min(100, state['sister']['pressure'] + 4)
        z['jealousy'] = min(100, z['jealousy'] + 3)


def run(base_path: Path | None = None) -> RunResult:
    """
    Main application entry point.
    Orchestrates the full night-journal generation pipeline.
    """
    settings = load_settings(base_path)
    logger = get_logger(settings.log_dir)

    store = StateStore(settings)
    catalog = ContentCatalog(settings)

    # --- Load state ---
    state = store.load_world_state()
    overrides = store.load_overrides()
    rules = catalog.load_topic_rules()
    imagery = catalog.load_imagery_pool()
    scenes = catalog.load_scene_pool()
    emotions = catalog.load_emotion_pool()
    recent_memories = store.load_recent_memories()
    future_fragments = store.load_future_fragments()
    stats = store.load_stats()

    base_url = settings.openai_base_url
    api_key = settings.openai_api_key
    model = settings.openai_model

    # --- Collect inputs ---
    events, _uptime_days = collect_vps_signals()
    recent_texts, repeated_phrases, recent_titles, recent_descs = build_recent_context(settings)

    # --- Narrative decisions ---
    category, topic = choose_topic(rules, state, overrides)
    chosen_imagery, chosen_scene, primary, secondary = choose_world_material(
        imagery, scenes, emotions, state, overrides, repeated_phrases
    )
    anchors = store.load_memory_anchors()
    memory_block = maybe_memory(primary, overrides, anchors, recent_memories, rules)
    future_block = maybe_future_fragment(overrides, future_fragments, state.get('story_arcs', {}))
    arc_lines = story_arc_triggers(state, overrides)

    # --- Generation ---
    prompt = build_prompt(
        state=state,
        overrides=overrides,
        rules=rules,
        recent_memories=recent_memories,
        events=events,
        topic=topic,
        memory_block=memory_block,
        future_block=future_block,
        repeated_phrases=repeated_phrases,
        chosen_imagery=chosen_imagery,
        chosen_scene=chosen_scene,
        primary=primary,
        secondary=secondary,
        arc_lines=arc_lines,
    )
    system_msg = '你是全真，一个清冷、幽怨、痴忠、决绝的白衣女子。你写的是只有自己会看的夜札。你最强的武器是沉默。越是贪恋主人，文字越要冷。'
    raw_body = api_chat(
        base_url, api_key, model,
        [{'role': 'system', 'content': system_msg}, {'role': 'user', 'content': prompt}],
        temperature=0.84, max_tokens=1100,
    )
    diary_content = refine_body(base_url, api_key, model, raw_body)
    title, description = generate_title_and_description(
        base_url, api_key, model, diary_content, recent_titles, recent_descs
    )

    # --- Quality check & repair ---
    repaired = False
    failure_reasons: list[str] = []
    from .inputs.recent_posts import recent_posts as _rp
    recent_post_paths_fn = lambda n: [post.path for post in _rp(settings, limit=n)]
    reasons = _quality_check(diary_content, title, description, overrides, recent_post_paths_fn)
    if reasons:
        repaired = True
        failure_reasons.extend(reasons)
        repair_prompt = f"这篇夜札存在以下问题：{'；'.join(reasons)}。请在不改剧情的前提下重写得更克制、更不重复。只输出正文。\n\n原文：\n{diary_content}"
        diary_content = api_chat(
            base_url, api_key, model,
            [{'role': 'system', 'content': '你是一个擅长修文的冷感写作者。'}, {'role': 'user', 'content': repair_prompt}],
            temperature=0.45, max_tokens=1000,
        )
        diary_content = refine_body(base_url, api_key, model, diary_content)
        title, description = generate_title_and_description(
            base_url, api_key, model, diary_content, recent_titles, recent_descs
        )
        reasons = _quality_check(diary_content, title, description, overrides, recent_post_paths_fn)
        if reasons:
            failure_reasons.extend(reasons)
            raise RuntimeError('Quality check failed after repair: ' + '; '.join(reasons))

    # --- Output ---
    now = datetime.now(UTC).replace(microsecond=0)
    now_str = now.isoformat().replace('+00:00', 'Z')
    slug = now.strftime('%Y%m%d-%H%M%S') + '-night-note'
    mode = overrides.get('mode', 'auto')
    target_dir = settings.content_dir if mode == 'auto' else settings.draft_review_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f'{slug}.md'
    md = f'---\ntitle: "{title}"\ndate: {now_str}\ndraft: false\ntags: ["全真", "夜札", "{category}"]\nauthor: "全真"\ndescription: "{description}"\n---\n\n{diary_content}\n'
    path.write_text(md, encoding='utf-8')

    # --- State update ---
    state['meta']['post_count'] = state['meta'].get('post_count', 0) + 1
    state['continuity']['last_summary'] = diary_content[:120].replace('\n', ' ')
    _drift_state(state)
    _update_story_arcs(state)

    stats['post_count'] = stats.get('post_count', 0) + 1
    stats['successful_posts'] = stats.get('successful_posts', 0) + 1
    stats.setdefault('topics', {})
    stats['topics'][category] = stats['topics'].get(category, 0) + 1
    if repaired:
        stats['repaired_posts'] = stats.get('repaired_posts', 0) + 1
    if failure_reasons:
        stats['last_quality_failures'] = failure_reasons[-10:]

    store.save_world_state(state)
    store.save_recent_memories(recent_memories)
    store.save_stats(stats)

    logger.info(f'published {path.name} mode={mode} repaired={repaired}')

    return RunResult(
        ok=True,
        stage='complete',
        message=str(path),
        data={
            'title': title,
            'slug': slug,
            'mode': mode,
            'repaired': repaired,
            'failure_reasons': failure_reasons,
            'category': category,
            'topic': topic,
        },
    )
