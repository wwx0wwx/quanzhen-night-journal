from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import GenerationTask, Persona, Post
from backend.schemas.persona import PersonaCreate, PersonaUpdate
from backend.utils.serde import json_dumps, json_loads
from backend.utils.text_integrity import inspect_text_integrity
from backend.utils.time import utcnow_iso


DEFAULT_LEXICON = {
    "high_cpu": "体内灵力激荡不休，像有无数细小电流在经脉间相撞。",
    "memory_pressure": "识海翻涌，旧事与新念一起拥来。",
    "memory_critical": "识海几乎决堤，许多念头挤在一处发烫。",
    "io_spike": "外界消息像雨点一样敲在门上。",
    "disk_warning": "落脚之处已逼仄，连呼吸都带着硬响。",
    "network_heavy": "四野风声不断，像有太多目光正擦过檐角。",
    "api_slow": "心意传出去很久，回音却迟迟未归。",
    "normal": "身心尚稳，灵台像擦净后的镜面。",
}


class PersonaEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def repair_corrupted_personas(self) -> list[int]:
        rows = await self.db.scalars(select(Persona).order_by(Persona.id.asc()))
        repaired: list[int] = []
        healthy_default: Persona | None = None

        for persona in rows:
            issues = self._integrity_issues(persona)
            if not issues:
                if healthy_default is None and persona.is_default:
                    healthy_default = persona
                continue

            persona.name = self._repair_text(persona.name, f"待修复人格 {persona.id}")
            persona.description = self._repair_text(
                persona.description,
                "该人格的部分文本在历史写入中发生损坏，已自动隔离并等待人工修订。",
            )
            persona.identity_setting = self._repair_text(
                persona.identity_setting,
                "这是一个已恢复的人格，请先补全核心身份设定后再启用自动写作。",
            )
            persona.worldview_setting = self._repair_text(
                persona.worldview_setting,
                "该人格的世界观文本已损坏，请结合既有文章风格人工补写。",
            )
            persona.language_style = self._repair_text(
                persona.language_style,
                "已恢复，建议按既有公开文章风格人工校准。",
            )
            persona.is_active = 0
            persona.updated_at = utcnow_iso()
            repaired.append(persona.id)

        if repaired:
            await self.db.execute(update(Persona).where(Persona.id.in_(repaired)).values(is_default=0))
            fallback = healthy_default or await self.db.scalar(select(Persona).where(Persona.id.notin_(repaired)).order_by(Persona.id.asc()))
            if fallback is None:
                fallback = await self.db.scalar(select(Persona).order_by(Persona.id.asc()))
            if fallback is not None:
                fallback.is_default = 1
                fallback.updated_at = utcnow_iso()

        await self.db.flush()
        return repaired

    async def create_persona(self, data: PersonaCreate) -> Persona:
        now = utcnow_iso()
        existing_count = await self.db.scalar(select(func.count()).select_from(Persona)) or 0
        persona = Persona(
            name=data.name,
            description=data.description,
            is_active=1 if data.is_active else 0,
            is_default=1 if (data.is_default or existing_count == 0) else 0,
            identity_setting=data.identity_setting,
            worldview_setting=data.worldview_setting,
            language_style=data.language_style,
            taboos=json_dumps(data.taboos),
            sensory_lexicon=json_dumps({**DEFAULT_LEXICON, **data.sensory_lexicon}),
            structure_preference=data.structure_preference,
            expression_intensity=data.expression_intensity,
            stability_params=json_dumps(data.stability_params),
            scene_pool=json_dumps(data.scene_pool),
            created_at=now,
            updated_at=now,
        )
        if persona.is_default:
            await self.db.execute(update(Persona).values(is_default=0))
        self.db.add(persona)
        await self.db.flush()
        return persona

    async def update_persona(self, persona_id: int, data: PersonaUpdate) -> Persona | None:
        persona = await self.db.get(Persona, persona_id)
        if persona is None:
            return None
        persona.name = data.name
        persona.description = data.description
        persona.is_active = 1 if data.is_active else 0
        persona.identity_setting = data.identity_setting
        persona.worldview_setting = data.worldview_setting
        persona.language_style = data.language_style
        persona.taboos = json_dumps(data.taboos)
        persona.sensory_lexicon = json_dumps({**DEFAULT_LEXICON, **data.sensory_lexicon})
        persona.structure_preference = data.structure_preference
        persona.expression_intensity = data.expression_intensity
        persona.stability_params = json_dumps(data.stability_params)
        persona.scene_pool = json_dumps(data.scene_pool)
        persona.updated_at = utcnow_iso()
        if data.is_default:
            await self.set_default(persona_id)
        await self.db.flush()
        return persona

    async def delete_persona(self, persona_id: int) -> bool:
        persona = await self.db.get(Persona, persona_id)
        if persona is None:
            return False
        await self.db.delete(persona)
        await self.db.flush()
        remaining = await self.db.scalars(select(Persona).order_by(Persona.id))
        first = next(iter(list(remaining)), None)
        if first is not None:
            first.is_default = 1
        return True

    async def set_default(self, persona_id: int) -> Persona | None:
        persona = await self.db.get(Persona, persona_id)
        if persona is None:
            return None
        await self.db.execute(update(Persona).values(is_default=0))
        persona.is_default = 1
        persona.updated_at = utcnow_iso()
        await self.db.flush()
        return persona

    async def get_active_persona(self) -> Persona | None:
        persona = await self.db.scalar(
            select(Persona).where(Persona.is_default == 1).order_by(Persona.id.asc())
        )
        if persona is None:
            persona = await self.db.scalar(select(Persona).order_by(Persona.id.asc()))
        return persona

    async def calculate_stability_score(self, persona_id: int) -> float:
        total_tasks = await self.db.scalar(
            select(func.count()).select_from(GenerationTask).where(GenerationTask.persona_id == persona_id)
        ) or 0
        published = await self.db.scalar(
            select(func.count()).select_from(Post).where(Post.persona_id == persona_id, Post.status == "published")
        ) or 0
        anti_count = await self.db.scalar(
            select(func.count()).select_from(GenerationTask).where(
                GenerationTask.persona_id == persona_id,
                GenerationTask.anti_perfection == 1,
            )
        ) or 0
        if total_tasks == 0:
            return 80.0
        publish_ratio = published / max(total_tasks, 1)
        anti_penalty = anti_count / max(total_tasks, 1)
        base = 55 + publish_ratio * 35 - anti_penalty * 20
        return max(0.0, min(100.0, round(base, 2)))

    def translate_sensory(self, persona: Persona, tags: list[str]) -> str:
        lexicon = json_loads(persona.sensory_lexicon, DEFAULT_LEXICON)
        if not tags:
            return lexicon.get("normal", DEFAULT_LEXICON["normal"])
        translated = [lexicon.get(tag, DEFAULT_LEXICON.get(tag, tag)) for tag in tags]
        return " ".join(translated)

    def _integrity_issues(self, persona: Persona) -> list[str]:
        issues: list[str] = []
        for value in (
            persona.name,
            persona.description,
            persona.identity_setting,
            persona.worldview_setting,
            persona.language_style,
        ):
            issues.extend(item.code for item in inspect_text_integrity(value))
        return issues

    def _repair_text(self, current: str, fallback: str) -> str:
        return fallback if inspect_text_integrity(current) else current
