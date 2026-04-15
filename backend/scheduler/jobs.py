from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.adapters.embedding_adapter import EmbeddingAdapter
from backend.adapters.llm_adapter import LLMAdapter
from backend.api.deps import get_encryptor
from backend.database import get_sessionmaker
from backend.engine.anti_perfection import AntiPerfectionEngine
from backend.engine.config_store import ConfigStore
from backend.engine.context_builder import ContextBuilder
from backend.engine.cost_monitor import CostMonitor
from backend.engine.digital_stamp import DigitalStampGenerator
from backend.engine.event_engine import EventEngine
from backend.engine.generation_orchestrator import GenerationOrchestrator
from backend.engine.memory_engine import MemoryEngine
from backend.engine.notification_manager import NotificationManager
from backend.engine.persona_engine import PersonaEngine
from backend.engine.prompt_builder import PromptBuilder
from backend.engine.qa_engine import QAEngine
from backend.engine.sensory_engine import SensoryEngine
from backend.publisher.registry import PublisherRegistry
from backend.utils.default_persona import (
    apply_default_quanzhen_to_persona,
    build_default_quanzhen_persona,
    is_legacy_default_quanzhen,
)
from backend.utils.time import utcnow_iso


async def _runtime():
    session_factory = get_sessionmaker()
    async with session_factory() as db:
        encryptor = await get_encryptor(db)
        config_store = ConfigStore(db, encryptor)
        persona_engine = PersonaEngine(db)
        memory_engine = MemoryEngine(db, config_store, EmbeddingAdapter(), LLMAdapter())
        qa_engine = QAEngine(db, config_store, EmbeddingAdapter())
        cost_monitor = CostMonitor(db, config_store)
        anti = AntiPerfectionEngine(db, config_store)
        context_builder = ContextBuilder(db, memory_engine, persona_engine, anti)
        orchestrator = GenerationOrchestrator(
            db=db,
            config_store=config_store,
            persona_engine=persona_engine,
            memory_engine=memory_engine,
            context_builder=context_builder,
            prompt_builder=PromptBuilder(),
            qa_engine=qa_engine,
            cost_monitor=cost_monitor,
            llm_adapter=LLMAdapter(),
            notification_manager=NotificationManager(config_store),
            publisher_registry=PublisherRegistry(),
            digital_stamp_generator=DigitalStampGenerator(),
        )
        yield db, config_store, persona_engine, memory_engine, qa_engine, cost_monitor, SensoryEngine(db, config_store), EventEngine(db, config_store), orchestrator


async def _ensure_seed_persona_in_session(db: AsyncSession, *, commit: bool) -> None:
    persona_engine = PersonaEngine(db)
    persona = await persona_engine.get_active_persona()
    changed = False

    if persona is None:
        await persona_engine.create_persona(build_default_quanzhen_persona())
        changed = True
    elif is_legacy_default_quanzhen(persona):
        apply_default_quanzhen_to_persona(persona)
        changed = True

    if changed and commit:
        await db.commit()


async def ensure_seed_persona(db: AsyncSession | None = None) -> None:
    if db is not None:
        await _ensure_seed_persona_in_session(db, commit=False)
        return

    async for runtime_db, *_ in _runtime():
        await _ensure_seed_persona_in_session(runtime_db, commit=True)


async def scheduled_generation_job(*, slot_index: int = 0, scheduled_for: str | None = None) -> None:
    async for _db, config_store, persona_engine, _memory_engine, _qa, _cost, _sensory, event_engine, orchestrator in _runtime():
        initialized = await config_store.get("system.initialized", "0")
        if initialized != "1":
            return
        event = await event_engine.create_scheduler_event(
            source="scheduler",
            payload={
                "scheduled_at": utcnow_iso(),
                "scheduled_for": scheduled_for or utcnow_iso(),
                "slot_index": slot_index,
            },
            semantic_hint="定时发文任务触发" if slot_index == 0 else f"定时补发任务触发 #{slot_index + 1}",
        )
        persona = await persona_engine.get_active_persona()
        await orchestrator.execute(event, persona=persona)


async def sensory_sample_job() -> None:
    async for db, _config, _persona, _memory, _qa, _cost, sensory_engine, _event, _orchestrator in _runtime():
        await sensory_engine.sample()
        await db.commit()


async def memory_decay_job() -> None:
    async for db, _config, _persona, memory_engine, _qa, _cost, _sensory, _event, _orchestrator in _runtime():
        await memory_engine.decay_memories()
        await db.commit()


async def memory_reflection_job() -> None:
    async for db, _config, persona_engine, memory_engine, _qa, _cost, _sensory, _event, _orchestrator in _runtime():
        persona = await persona_engine.get_active_persona()
        if persona:
            await memory_engine.run_reflection(persona.id)
            await db.commit()
