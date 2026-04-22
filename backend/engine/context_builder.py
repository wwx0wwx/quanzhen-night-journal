from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.engine.anti_perfection import AntiPerfectionEngine
from backend.engine.memory_engine import MemoryEngine
from backend.engine.persona_engine import PersonaEngine
from backend.engine.prompt_builder import GenerationContext, RecentPostContext
from backend.models import Event, GenerationTask, Persona, Post, SensorySnapshot
from backend.utils.serde import json_dumps, json_loads


class ContextBuilder:
    RECENT_POST_LIMIT = 4
    RECENT_ARTICLE_MEMORY_EXCLUDE_COUNT = 2
    RECENT_ARTICLE_MEMORY_EXCLUDE_HOURS = 72

    def __init__(
        self,
        db: AsyncSession,
        memory_engine: MemoryEngine,
        persona_engine: PersonaEngine,
        anti_perfection_engine: AntiPerfectionEngine,
    ):
        self.db = db
        self.memory_engine = memory_engine
        self.persona_engine = persona_engine
        self.anti_perfection_engine = anti_perfection_engine

    async def build(self, task: GenerationTask, persona: Persona) -> tuple[GenerationContext, dict]:
        event = await self.db.get(Event, task.event_id) if task.event_id else None
        recent_posts = await self._get_recent_posts(persona.id)
        excluded_memory_ids = await self._get_recent_article_memory_ids(persona.id)
        query = self._build_search_query(task, persona, event)
        memory_hits = await self.memory_engine.search(
            query=query,
            persona_id=persona.id,
            top_k=5,
            exclude_memory_ids=excluded_memory_ids,
        )

        snapshot = await self._get_latest_valid_snapshot()
        sensory_text = ""
        if snapshot and not snapshot.is_in_blind_zone:
            sensory_text = self.persona_engine.translate_sensory(persona, json_loads(snapshot.tags, []))

        anti = await self.anti_perfection_engine.should_trigger(snapshot, persona)
        context = GenerationContext(
            persona=persona,
            memory_hits=memory_hits,
            sensory_text=sensory_text,
            sensory_snapshot=snapshot,
            event=event,
            recent_posts=recent_posts,
            anti_perfection=anti,
            cold_start=(len(memory_hits) == 0),
        )
        snapshot_dict = {
            "persona_id": persona.id,
            "event_id": event.id if event else None,
            "event_type": event.event_type if event else None,
            "memory_hits": [hit.model_dump() for hit in memory_hits],
            "excluded_memory_ids": excluded_memory_ids,
            "sensory_snapshot_id": snapshot.id if snapshot else None,
            "sensory_text": sensory_text,
            "recent_posts": [
                {
                    "id": item.id,
                    "title": item.title,
                    "summary": item.summary,
                    "published_at": item.published_at,
                }
                for item in recent_posts
            ],
            "anti_perfection": anti,
            "cold_start": context.cold_start,
        }
        return context, snapshot_dict

    async def _get_latest_valid_snapshot(self) -> SensorySnapshot | None:
        rows = await self.db.scalars(
            select(SensorySnapshot)
            .where(SensorySnapshot.is_in_blind_zone == 0)
            .order_by(desc(SensorySnapshot.sampled_at))
            .limit(1)
        )
        return rows.first()

    def _build_search_query(self, task: GenerationTask, persona: Persona, event: Event | None) -> str:
        pieces = [persona.identity_setting, persona.worldview_setting]
        if event:
            pieces.extend([event.normalized_semantic, event.source, event.event_type])
        if task.context_snapshot:
            pieces.append(task.context_snapshot)
        return " ".join(piece for piece in pieces if piece)

    async def _get_recent_posts(self, persona_id: int) -> list[RecentPostContext]:
        rows = await self.db.scalars(
            select(Post)
            .where(Post.persona_id == persona_id, Post.status == "published")
            .order_by(desc(Post.published_at), desc(Post.id))
            .limit(self.RECENT_POST_LIMIT)
        )
        return [
            RecentPostContext(
                id=post.id,
                title=post.title,
                summary=post.summary,
                published_at=post.published_at,
            )
            for post in rows
        ]

    async def _get_recent_article_memory_ids(self, persona_id: int) -> list[int]:
        return await self.memory_engine.recent_article_memory_ids(
            persona_id=persona_id,
            limit=self.RECENT_ARTICLE_MEMORY_EXCLUDE_COUNT,
            hours=self.RECENT_ARTICLE_MEMORY_EXCLUDE_HOURS,
        )
