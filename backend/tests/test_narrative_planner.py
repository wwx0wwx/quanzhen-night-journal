from __future__ import annotations

from backend.engine.narrative_planner import WORLD_PHASES, NarrativePlanner, NarrativeState


def test_phase_progression_covers_prime_years():
    planner = NarrativePlanner()
    assert planner.phase_for_year(0.5)["id"] == "shadow_stable"
    assert planner.phase_for_year(3.0)["id"] == "misread_deepens"
    assert planner.phase_for_year(5.0)["id"] == "shadow_tightens"
    assert planner.phase_for_year(7.0)["id"] == "favor_surfaces"
    assert planner.phase_for_year(9.0)["id"] == "year_of_choice"
    assert WORLD_PHASES[-1]["year_end"] == 10


def test_posts_per_year_maps_months_to_years():
    """Daily posts for ~4 months @ 15 posts/year ≈ 8 world years."""
    posts = 120  # ~4 months daily
    years = posts / 15
    assert 6 <= years <= 10


def test_task_card_rotates_relation_and_scene():
    planner = NarrativePlanner()
    pool = [
        {"时间": "深夜", "地点": "王府廊下", "天气": "微雪", "方向": "守夜"},
        {"时间": "黄昏", "地点": "渡口", "天气": "江风", "方向": "送姐姐"},
        {"时间": "凌晨", "地点": "密林", "天气": "浓雾", "方向": "密令归来"},
        {"时间": "午后", "地点": "集市", "天气": "晴", "方向": "微服"},
        {"时间": "清晨", "地点": "药铺街巷", "天气": "薄雾", "方向": "买伤药"},
    ]
    state = NarrativeState()
    tones = []
    buckets = []
    for i in range(14):
        card = planner.build_task_card(
            persona_id=1,
            scene_pool=pool,
            state=state,
            posts_per_world_year=15,
            seed=f"t-{i}",
        )
        tones.append(card.relation_tone)
        buckets.append(card.scene_bucket)
        state = planner.advance_after_publish(
            state,
            card,
            title=f"题{i}",
            content=f"# 题{i}\n\n残月斜在西边第{i}夜，我从北山道折回。",
            posts_per_world_year=15,
        )
    # Within 7 posts after start, 占有 must appear due to force rule.
    assert "占有" in tones[:8]
    # Scene buckets should not be a single type.
    assert len(set(buckets)) >= 3
    assert state.posts_published == 14
    assert state.world_year > 0.5


def test_opening_similarity_detects_near_clone():
    a = "残月斜在西边，天还没亮透。我从北山道折回来时，马已"
    b = "残月斜在西边，天还没亮透。我从北山道折回来时，马已疲"
    score = NarrativePlanner.opening_similarity(a, b)
    assert score >= 0.85
    c = "午后集市人声乱，我把剑藏在伞里，跟在王爷半步之后。"
    assert NarrativePlanner.opening_similarity(a, c) < 0.7


def test_task_card_block_contains_worldline():
    planner = NarrativePlanner()
    card = planner.build_task_card(
        persona_id=1,
        scene_pool=[{"时间": "入夜", "地点": "屋顶", "天气": "繁星", "方向": "独坐"}],
        state=NarrativeState(world_year=4.2, posts_published=63),
        seed="block",
    )
    block = planner.format_task_card_block(card)
    assert "本篇任务卡" in block
    assert "关系主音" in block
    assert "世界线" in block
    assert card.phase_name


def test_state_roundtrip_json():
    state = NarrativeState(
        posts_published=10,
        world_year=0.66,
        last_relation_tones=["守护", "占有"],
        sister_in_residence=True,
        posts_since_easter_egg=3,
        last_easter_egg_ids=["rouge_market"],
    )
    restored = NarrativeState.from_json(state.to_json())
    assert restored.posts_published == 10
    assert restored.sister_in_residence is True
    assert restored.last_relation_tones == ["守护", "占有"]
    assert restored.posts_since_easter_egg == 3
    assert restored.last_easter_egg_ids == ["rouge_market"]


def test_easter_egg_fires_after_gap_and_includes_idle_beats():
    planner = NarrativePlanner()
    state = NarrativeState(posts_published=20, world_year=1.3, posts_since_easter_egg=14)
    card = planner.build_task_card(
        persona_id=1,
        scene_pool=[{"时间": "深夜", "地点": "廊下", "天气": "雪", "方向": "守夜"}],
        state=state,
        seed="egg-force",
    )
    assert card.scene_bucket == "闲笔彩蛋"
    assert card.easter_egg_id
    assert "小彩蛋" in " ".join(card.requirements) or card.easter_egg_id
    block = planner.format_task_card_block(card)
    assert "小彩蛋" in block
    # Advance resets counter.
    new_state = planner.advance_after_publish(
        state, card, title="粉", content="# 粉\n\n午后香粉气淡淡的，我把瓷盒按进袖里。", posts_per_world_year=15
    )
    assert new_state.posts_since_easter_egg == 0
    assert card.easter_egg_id in new_state.last_easter_egg_ids


def test_new_clever_easter_eggs_in_catalog():
    from backend.engine.narrative_planner import EASTER_EGG_CATALOG

    ids = {egg["id"] for egg in EASTER_EGG_CATALOG}
    assert "steal_hair_lesson" in ids
    assert "new_tassel_unused" in ids
    hair = next(e for e in EASTER_EGG_CATALOG if e["id"] == "steal_hair_lesson")
    tassel = next(e for e in EASTER_EGG_CATALOG if e["id"] == "new_tassel_unused")
    assert "偷学" in hair["scene"]["方向"] or "偷看" in hair["scene"]["方向"]
    assert "新穗" in tassel["scene"]["方向"] and "旧穗" in tassel["scene"]["方向"]


def test_easter_egg_suppressed_within_min_gap():
    planner = NarrativePlanner()
    state = NarrativeState(posts_published=5, posts_since_easter_egg=2)
    # Even with many seeds, min gap should block eggs.
    eggs = 0
    for i in range(20):
        card = planner.build_task_card(
            persona_id=1,
            scene_pool=[{"时间": "深夜", "地点": "廊下", "天气": "雪", "方向": "守夜"}],
            state=state,
            seed=f"no-egg-{i}",
        )
        if card.easter_egg_id:
            eggs += 1
    assert eggs == 0
