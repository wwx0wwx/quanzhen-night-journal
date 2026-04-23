from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.engine.config_store import ConfigStore
from backend.models import Persona, SensorySnapshot
from backend.utils.serde import json_loads


class AntiPerfectionEngine:
    def __init__(self, db: AsyncSession, config_store: ConfigStore):
        self.db = db
        self.config_store = config_store

    async def should_trigger(self, snapshot: SensorySnapshot | None, persona: Persona) -> bool:
        if snapshot is None:
            return False
        enabled = await self.config_store.get("anti_perfection.enabled", "1")
        if enabled != "1":
            return False
        tags = set(json_loads(snapshot.tags, []))
        immediate = ("memory_critical" in tags and "io_spike" in tags) or (
            "memory_critical" in tags and "high_cpu" in tags
        )
        if immediate:
            return True
        recent = await self.db.scalars(select(SensorySnapshot).order_by(desc(SensorySnapshot.sampled_at)).limit(3))
        recent_tags = [set(json_loads(item.tags, [])) for item in recent]
        return len(recent_tags) == 3 and all("high_cpu" in entry for entry in recent_tags)

    def modify_generation_params(self, persona: Persona) -> dict:
        params = json_loads(persona.stability_params, {"temperature_base": 0.7, "temperature_range": [0.3, 1.2]})
        upper = params.get("temperature_range", [0.3, 1.2])[-1]
        return {
            "temperature": upper,
            "max_tokens_scale": 0.35,
            "extra_prompt": "允许出现轻微碎片化、不稳定、意识流式跳接，但仍保持人格一致。",
        }
