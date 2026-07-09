from __future__ import annotations

import asyncio

from backend.adapters.embedding_adapter import EmbeddingAdapter
from backend.adapters.llm_adapter import LLMAdapter
from backend.database import get_sessionmaker
from backend.engine.config_store import ConfigStore
from backend.engine.memory_engine import MemoryEngine
from backend.schemas.memory import MemoryCreate


def test_keyword_fallback_finds_chinese_without_spaces(authed_client):
    async def exercise() -> list:
        session_factory = get_sessionmaker()
        async with session_factory() as db:
            engine = MemoryEngine(db, ConfigStore(db), EmbeddingAdapter(), LLMAdapter())
            await engine.create_memory(
                MemoryCreate(
                    persona_id=1,
                    level="L0",
                    content="我靠在廊柱旁，手按剑鞘，听着檐下雨声。",
                    summary="廊柱旁听雨。",
                    tags=["core"],
                    source="hand_written",
                    weight=1.0,
                    review_status="reviewed",
                    decay_strategy="standard",
                    is_core=True,
                )
            )
            await db.commit()
            return await engine.search_fallback_keyword("廊柱剑鞘", persona_id=1, top_k=5)

    hits = asyncio.run(exercise())
    assert hits
    assert hits[0].id > 0


def test_candidate_limit_bounds_search_pool(authed_client):
    async def exercise() -> int:
        session_factory = get_sessionmaker()
        async with session_factory() as db:
            store = ConfigStore(db)
            await store.set("memory.search_candidate_limit", "5", category="memory")
            await store.set("memory.search_recent_limit", "3", category="memory")
            await store.set("memory.search_core_limit", "2", category="memory")
            engine = MemoryEngine(db, store, EmbeddingAdapter(), LLMAdapter())
            for index in range(12):
                await engine.create_memory(
                    MemoryCreate(
                        persona_id=1,
                        level="L2",
                        content=f"夜记片段{index} 雨声与刀光",
                        summary=f"片段{index}",
                        tags=["auto"],
                        source="auto_summary",
                        weight=1.0,
                        review_status="unreviewed",
                        decay_strategy="standard",
                        is_core=False,
                    )
                )
            await db.commit()
            candidates = await engine._candidate_memories(
                persona_id=1,
                level_filter=None,
                exclude_memory_ids=None,
            )
            return len(candidates)

    count = asyncio.run(exercise())
    assert count <= 5
