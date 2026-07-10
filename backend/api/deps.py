from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.adapters.embedding_adapter import EmbeddingAdapter
from backend.adapters.llm_adapter import LLMAdapter
from backend.database import get_session
from backend.engine.config_store import ConfigStore
from backend.engine.cost_monitor import CostMonitor
from backend.engine.event_engine import EventEngine
from backend.engine.generation_orchestrator import GenerationOrchestrator
from backend.engine.memory_engine import MemoryEngine
from backend.engine.persona_engine import PersonaEngine
from backend.engine.qa_engine import QAEngine
from backend.engine.runtime_factory import build_generation_runtime
from backend.engine.sensory_engine import SensoryEngine
from backend.engine.site_runtime import SiteRuntimeManager
from backend.security.encryption import ConfigEncryptor, ensure_encryptor


async def get_encryptor(db: AsyncSession = Depends(get_session)) -> ConfigEncryptor:
    encryptor, created = await ensure_encryptor(db)
    if created:
        await db.commit()
    return encryptor


async def get_config_store(
    db: AsyncSession = Depends(get_session),
    encryptor: ConfigEncryptor = Depends(get_encryptor),
) -> ConfigStore:
    return ConfigStore(db, encryptor)


async def get_persona_engine(db: AsyncSession = Depends(get_session)) -> PersonaEngine:
    return PersonaEngine(db)


async def get_memory_engine(
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
) -> MemoryEngine:
    return MemoryEngine(db, config_store, EmbeddingAdapter(), LLMAdapter())


async def get_qa_engine(
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
) -> QAEngine:
    return QAEngine(db, config_store, EmbeddingAdapter())


async def get_cost_monitor(
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
) -> CostMonitor:
    return CostMonitor(db, config_store)


async def get_sensory_engine(
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
) -> SensoryEngine:
    return SensoryEngine(db, config_store)


async def get_event_engine(
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
) -> EventEngine:
    return EventEngine(db, config_store)


async def get_orchestrator(
    db: AsyncSession = Depends(get_session),
    encryptor: ConfigEncryptor = Depends(get_encryptor),
) -> GenerationOrchestrator:
    *_rest, orchestrator = build_generation_runtime(db, encryptor)
    return orchestrator


async def get_site_runtime_manager(
    config_store: ConfigStore = Depends(get_config_store),
) -> SiteRuntimeManager:
    return SiteRuntimeManager(config_store)
