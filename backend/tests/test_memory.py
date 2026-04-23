from __future__ import annotations

import asyncio
import sqlite3

from backend.adapters.embedding_adapter import EmbeddingAdapter
from backend.adapters.llm_adapter import LLMAdapter
from backend.config import get_settings
from backend.database import get_sessionmaker, init_database
from backend.engine.config_store import ConfigStore
from backend.engine.memory_engine import MemoryEngine
from backend.models import Post
from backend.schemas.memory import MemoryCreate


def test_memory_create_and_search(authed_client):
    created = authed_client.post(
        "/api/memories",
        json={
            "persona_id": 1,
            "level": "L0",
            "content": "机箱风声贴着木纹走过去，像潮水很慢地退。",
            "summary": "机箱风声像潮水退去。",
            "tags": ["core"],
            "source": "hand_written",
            "weight": 1.0,
            "review_status": "reviewed",
            "decay_strategy": "standard",
            "is_core": True,
        },
    )
    assert created.status_code == 200

    searched = authed_client.post(
        "/api/memories/search",
        json={"query": "风声 机箱", "persona_id": 1, "top_k": 5},
    )
    assert searched.status_code == 200
    assert searched.json()["data"]


def test_article_memory_uses_structured_summary_and_recent_exclusion(authed_client):
    async def exercise() -> None:
        session_factory = get_sessionmaker()
        async with session_factory() as db:
            engine = MemoryEngine(db, ConfigStore(db), EmbeddingAdapter(), LLMAdapter())
            article_memory = await engine.create_from_article(
                Post(
                    title="檐外消息撞得门环响",
                    slug="1-全真夜记",
                    front_matter="{}",
                    content_markdown=(
                        "# 檐外消息撞得门环响\n\n我靠在廊柱，站在王爷书房半步外。\n\n雪又开始落了，落在我剑鞘上。"
                    ),
                    summary="我靠在廊柱，站在王爷书房半步外。",
                    status="published",
                    persona_id=1,
                    task_id=1,
                    published_at="2026-04-15T21:02:29+00:00",
                    revision=1,
                    publish_target="hugo",
                    digital_stamp="",
                    review_info="{}",
                    created_at="2026-04-15T21:02:29+00:00",
                    updated_at="2026-04-15T21:02:29+00:00",
                ),
                persona_id=1,
            )
            article_memory.created_at = "2026-04-15T21:02:29+00:00"

            recent_hand_written = await engine.create_memory(
                MemoryCreate(
                    persona_id=1,
                    level="L0",
                    content="廊柱旁的风贴着剑鞘过去。",
                    summary="廊柱旁的风贴着剑鞘过去。",
                    tags=["core"],
                    source="hand_written",
                    weight=1.0,
                    review_status="reviewed",
                    decay_strategy="standard",
                    is_core=True,
                )
            )
            await db.commit()

            assert article_memory.content.startswith("标题：檐外消息撞得门环响")
            assert article_memory.content != (
                "# 檐外消息撞得门环响\n\n我靠在廊柱，站在王爷书房半步外。\n\n雪又开始落了，落在我剑鞘上。"
            )
            assert "用途：用于保持长期叙事连续性" in article_memory.content
            assert "我靠在廊柱，站在王爷书房半步外。" not in article_memory.content.splitlines()[-1]

            excluded_ids = await engine.recent_article_memory_ids(persona_id=1, limit=2, hours=72)
            assert article_memory.id in excluded_ids

            hits = await engine.search(
                query="廊柱 剑鞘",
                persona_id=1,
                top_k=5,
                exclude_memory_ids=excluded_ids,
            )
            assert all(hit.id != article_memory.id for hit in hits)
            assert any(hit.id == recent_hand_written.id for hit in hits)

    asyncio.run(exercise())


def test_init_database_normalizes_legacy_article_memories(authed_client):
    settings = get_settings()
    conn = sqlite3.connect(settings.database_path)
    conn.execute(
        """
        INSERT INTO posts (
            id, title, slug, front_matter, content_markdown, summary, status,
            persona_id, task_id, published_at, revision, publish_target,
            digital_stamp, review_info, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            99,
            "檐外消息撞得门环响",
            "1-quanzhen-night-journal",
            "{}",
            "# 全真夜记\n\n我靠在廊柱，站在王爷书房半步外。\n\n雪又开始落了，落在我剑鞘上。",
            "我靠在廊柱，站在王爷书房半步外。",
            "published",
            1,
            1,
            "2026-04-15T21:02:29+00:00",
            1,
            "hugo",
            "",
            "{}",
            "2026-04-15T21:02:29+00:00",
            "2026-04-15T21:02:29+00:00",
        ),
    )
    conn.execute(
        """
        INSERT INTO memories (
            id, persona_id, level, content, summary, tags, source, weight,
            review_status, decay_strategy, is_core, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            199,
            1,
            "L2",
            "# 全真夜记\n\n我靠在廊柱，站在王爷书房半步外。\n\n雪又开始落了，落在我剑鞘上。",
            "旧版全文记忆",
            '["article"]',
            "article",
            1.0,
            "unreviewed",
            "standard",
            0,
            "2026-04-15T21:02:29+00:00",
        ),
    )
    conn.commit()
    conn.close()

    asyncio.run(init_database())

    conn = sqlite3.connect(settings.database_path)
    content, summary, tags = conn.execute("SELECT content, summary, tags FROM memories WHERE id = 199").fetchone()
    conn.close()

    assert content.startswith("标题：檐外消息撞得门环响")
    assert "开场动作：我靠在廊柱，站在王爷书房半步外。" in content
    assert "收束状态：雪又开始落了，落在我剑鞘上。" in content
    assert content.count("用途：用于保持长期叙事连续性") == 1
    assert summary == "我靠在廊柱，站在王爷书房半步外。"
    assert tags == '["article", "post:99"]'
