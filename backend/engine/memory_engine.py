from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta

from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.adapters.embedding_adapter import EmbeddingAdapter, EmbeddingUnavailableError
from backend.adapters.llm_adapter import LLMAdapter
from backend.engine.config_store import ConfigStore
from backend.models import Memory, MemoryVector, Persona, Post
from backend.schemas.memory import MemoryCreate, MemoryHit
from backend.utils.serde import json_dumps, json_loads
from backend.utils.time import UTC, utcnow, utcnow_iso


LEVEL_WEIGHT = {"L0": 4.0, "L1": 3.0, "L2": 2.0, "L3": 1.0}

logger = logging.getLogger(__name__)
SOURCE_WEIGHT = {
    "hand_written": 3.0,
    "reflection": 2.5,
    "auto_summary": 2.0,
    "article": 1.5,
    "import": 1.0,
}


class MemoryEngine:
    ARTICLE_MEMORY_SNIPPET_LIMIT = 48

    def __init__(
        self,
        db: AsyncSession,
        config_store: ConfigStore,
        embedding_adapter: EmbeddingAdapter,
        llm_adapter: LLMAdapter | None = None,
    ):
        self.db = db
        self.config_store = config_store
        self.embedding_adapter = embedding_adapter
        self.llm_adapter = llm_adapter or LLMAdapter()

    async def create_memory(self, data: MemoryCreate) -> Memory:
        memory = Memory(
            persona_id=data.persona_id,
            level=data.level,
            content=data.content,
            summary=data.summary,
            tags=json_dumps(data.tags),
            source=data.source,
            weight=data.weight,
            time_range_start=data.time_range_start,
            time_range_end=data.time_range_end,
            review_status=data.review_status,
            decay_strategy=data.decay_strategy,
            is_core=1 if data.is_core else 0,
            created_at=utcnow_iso(),
            last_accessed_at=None,
        )
        self.db.add(memory)
        await self.db.flush()
        await self.embed_and_store(memory.id, memory.content)
        return memory

    async def embed_and_store(self, memory_id: int, text: str) -> None:
        base_url = await self.config_store.get("embedding.base_url", "") or await self.config_store.get("llm.base_url", "")
        api_key = await self.config_store.get("embedding.api_key", "") or await self.config_store.get("llm.api_key", "")
        model_id = await self.config_store.get("embedding.model_id", "") or await self.config_store.get("llm.model_id", "")
        dimensions = int(await self.config_store.get("embedding.dimensions", "1536") or 1536)
        try:
            vector = (
                await self.embedding_adapter.embed(
                    base_url=base_url or "",
                    api_key=api_key or "",
                    model_id=model_id or "",
                    texts=[text],
                    dimensions=dimensions,
                )
            )[0]
        except EmbeddingUnavailableError:
            logger.warning("embedding unavailable for memory %s, skipping vector store", memory_id)
            return
        existing = await self.db.get(MemoryVector, memory_id)
        if existing is None:
            self.db.add(MemoryVector(memory_id=memory_id, embedding=json_dumps(vector)))
        else:
            existing.embedding = json_dumps(vector)
        await self.db.flush()

    async def search(
        self,
        query: str,
        persona_id: int,
        top_k: int = 5,
        level_filter: list[str] | None = None,
        exclude_memory_ids: list[int] | None = None,
    ) -> list[MemoryHit]:
        stmt = select(Memory).where(Memory.persona_id == persona_id)
        if level_filter:
            stmt = stmt.where(Memory.level.in_(level_filter))
        excluded = set(exclude_memory_ids or [])
        if excluded:
            stmt = stmt.where(Memory.id.notin_(excluded))
        rows = await self.db.scalars(stmt.order_by(desc(Memory.created_at)))
        memories = list(rows)
        if not memories:
            return []

        try:
            base_url = await self.config_store.get("embedding.base_url", "") or await self.config_store.get("llm.base_url", "")
            api_key = await self.config_store.get("embedding.api_key", "") or await self.config_store.get("llm.api_key", "")
            model_id = await self.config_store.get("embedding.model_id", "") or await self.config_store.get("llm.model_id", "")
            query_vector = (
                await self.embedding_adapter.embed(
                    base_url=base_url or "",
                    api_key=api_key or "",
                    model_id=model_id or "",
                    texts=[query],
                )
            )[0]
            vector_rows = await self.db.scalars(
                select(MemoryVector).where(MemoryVector.memory_id.in_([memory.id for memory in memories]))
            )
            vector_map = {item.memory_id: json_loads(item.embedding, []) for item in vector_rows}
            hits: list[MemoryHit] = []
            for memory in memories:
                vector = vector_map.get(memory.id)
                similarity = self.embedding_adapter.cosine_similarity(query_vector, vector or [])
                weighted = similarity * self._score_multiplier(memory)
                hits.append(
                    MemoryHit(
                        id=memory.id,
                        level=memory.level,
                        similarity=round(similarity, 4),
                        weighted_score=round(weighted, 4),
                        content=memory.content,
                        summary=memory.summary,
                    )
                )
            hits.sort(key=lambda item: item.weighted_score, reverse=True)
            return hits[:top_k]
        except (EmbeddingUnavailableError, ValueError, TypeError, KeyError):
            return await self.search_fallback_keyword(
                query,
                persona_id,
                top_k=top_k,
                exclude_memory_ids=exclude_memory_ids,
            )

    async def search_fallback_keyword(
        self,
        query: str,
        persona_id: int,
        top_k: int = 5,
        exclude_memory_ids: list[int] | None = None,
    ) -> list[MemoryHit]:
        query_tokens = {token for token in query.lower().split() if token}
        excluded = set(exclude_memory_ids or [])
        rows = await self.db.scalars(select(Memory).where(Memory.persona_id == persona_id))
        hits: list[MemoryHit] = []
        for memory in rows:
            if memory.id in excluded:
                continue
            text = f"{memory.content} {memory.summary}".lower()
            overlap = len([token for token in query_tokens if token in text])
            score = overlap * self._score_multiplier(memory)
            if overlap:
                hits.append(
                    MemoryHit(
                        id=memory.id,
                        level=memory.level,
                        similarity=float(overlap),
                        weighted_score=round(score, 4),
                        content=memory.content,
                        summary=memory.summary,
                    )
                )
        hits.sort(key=lambda item: item.weighted_score, reverse=True)
        return hits[:top_k]

    async def decay_memories(self) -> int:
        rows = await self.db.scalars(select(Memory))
        affected = 0
        now = utcnow()
        for memory in rows:
            created = self._parse_time(memory.created_at)
            age_days = (now - created).days
            if memory.level == "L3":
                if age_days > 60:
                    await self.db.execute(delete(MemoryVector).where(MemoryVector.memory_id == memory.id))
                    await self.db.delete(memory)
                    affected += 1
                    continue
                if age_days > 30:
                    memory.weight *= 0.5
                    affected += 1
            elif memory.level == "L2" and age_days > 90:
                memory.weight *= 0.7
                affected += 1
            elif memory.level == "L1" and age_days > 365:
                memory.weight *= 0.9
                affected += 1
        await self.db.flush()
        return affected

    async def run_reflection(self, persona_id: int) -> Memory | None:
        rows = await self.db.scalars(
            select(Memory).where(Memory.persona_id == persona_id, Memory.level == "L2").order_by(desc(Memory.created_at))
        )
        recent = [item for item in rows if self._parse_time(item.created_at) >= utcnow() - timedelta(days=30)]
        if not recent:
            return None
        persona = await self.db.get(Persona, persona_id)
        prompt = "\n".join(f"- {item.summary or item.content[:80]}" for item in recent[:12])
        base_url = await self.config_store.get("llm.base_url", "")
        api_key = await self.config_store.get("llm.api_key", "")
        model_id = await self.config_store.get("llm.model_id", "")
        content, _, _ = await self.llm_adapter.chat(
            base_url=base_url or "",
            api_key=api_key or "",
            model_id=model_id or "",
            messages=[
                {"role": "system", "content": f"你在为人格 {persona.name if persona else '全真'} 总结阶段性记忆。"},
                {"role": "user", "content": f"请把这些近 30 天记忆压缩成 120 字内阶段摘要：\n{prompt}"},
            ],
            temperature=0.3,
            max_tokens=180,
        )
        return await self.create_memory(
            MemoryCreate(
                persona_id=persona_id,
                level="L1",
                content=content.strip(),
                summary=content.strip()[:120],
                tags=["reflection"],
                source="reflection",
            )
        )

    async def promote(self, memory_id: int) -> Memory | None:
        memory = await self.db.get(Memory, memory_id)
        if memory is None:
            return None
        next_level = {"L2": "L1", "L1": "L0"}.get(memory.level)
        if next_level is None:
            return memory
        memory.level = next_level
        memory.review_status = "promoted"
        await self.db.flush()
        return memory

    async def calculate_coherence_score(self, persona_id: int) -> float:
        hits = await self.search("核心记忆", persona_id=persona_id, top_k=12)
        if len(hits) <= 1:
            return 82.0
        mean = sum(item.weighted_score for item in hits) / len(hits)
        variance = sum((item.weighted_score - mean) ** 2 for item in hits) / len(hits)
        score = 100 - min(50, variance * 100)
        return round(max(0.0, score), 2)

    async def create_from_article(self, post: Post, persona_id: int) -> Memory:
        content = self._build_article_memory_content(post)
        summary = (post.summary or post.title)[:180]
        return await self.create_memory(
            MemoryCreate(
                persona_id=persona_id,
                level="L2",
                content=content,
                summary=summary,
                tags=["article", f"post:{post.id}"],
                source="article",
            )
        )

    async def recent_article_memory_ids(self, persona_id: int, *, limit: int, hours: int) -> list[int]:
        rows = await self.db.scalars(
            select(Memory)
            .where(Memory.persona_id == persona_id, Memory.source == "article")
            .order_by(desc(Memory.created_at), desc(Memory.id))
        )
        now = utcnow()
        selected: list[int] = []
        for index, item in enumerate(rows):
            age_hours = (now - self._parse_time(item.created_at)).total_seconds() / 3600
            if index < limit or age_hours <= hours:
                selected.append(item.id)
        return selected

    async def stats(self) -> dict:
        rows = await self.db.execute(
            select(Memory.level, func.count()).group_by(Memory.level).order_by(Memory.level.asc())
        )
        counts = {level: count for level, count in rows}
        total = sum(counts.values())
        return {"levels": counts, "total": total}

    def _score_multiplier(self, memory: Memory) -> float:
        created = self._parse_time(memory.created_at)
        age_days = max(0, (utcnow() - created).days)
        decay_days = 90 if memory.level == "L0" else 45
        time_decay = math.exp(-age_days / decay_days) if decay_days else 1.0
        return (
            LEVEL_WEIGHT.get(memory.level, 1.0)
            * time_decay
            * SOURCE_WEIGHT.get(memory.source, 1.0)
            * float(memory.weight or 1.0)
        )

    def _parse_time(self, value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)

    def _build_article_memory_content(self, post: Post) -> str:
        lines = [line.strip() for line in post.content_markdown.splitlines() if line.strip() and not line.startswith("#")]
        opening = lines[0][: self.ARTICLE_MEMORY_SNIPPET_LIMIT] if lines else (post.summary or post.title)[: self.ARTICLE_MEMORY_SNIPPET_LIMIT]
        closing = lines[-1][: self.ARTICLE_MEMORY_SNIPPET_LIMIT] if lines else opening
        return "\n".join(
            [
                f"标题：{post.title}",
                f"发布时间：{post.published_at or post.created_at}",
                f"摘要：{(post.summary or post.title)[:180]}",
                f"开场动作：{opening}",
                f"收束状态：{closing}",
                "用途：用于保持长期叙事连续性，但新稿不得直接复写上述场景、动作或措辞。",
            ]
        ).strip()
