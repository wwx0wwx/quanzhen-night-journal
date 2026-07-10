"""Single factory for generation runtime graph (API / scheduler / folder monitor)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.adapters.embedding_adapter import EmbeddingAdapter
from backend.adapters.llm_adapter import LLMAdapter
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
from backend.security.encryption import ConfigEncryptor


def build_generation_runtime(
    db: AsyncSession,
    encryptor: ConfigEncryptor,
) -> tuple[
    ConfigStore,
    PersonaEngine,
    MemoryEngine,
    QAEngine,
    CostMonitor,
    SensoryEngine,
    EventEngine,
    GenerationOrchestrator,
]:
    """Build a full orchestrator stack sharing one session and encryptor."""
    config_store = ConfigStore(db, encryptor)
    persona_engine = PersonaEngine(db)
    memory_engine = MemoryEngine(db, config_store, EmbeddingAdapter(), LLMAdapter())
    qa_engine = QAEngine(db, config_store, EmbeddingAdapter())
    cost_monitor = CostMonitor(db, config_store)
    sensory_engine = SensoryEngine(db, config_store)
    event_engine = EventEngine(db, config_store)
    anti = AntiPerfectionEngine(db, config_store)
    context_builder = ContextBuilder(
        db, memory_engine, persona_engine, anti, config_store=config_store
    )
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
    return (
        config_store,
        persona_engine,
        memory_engine,
        qa_engine,
        cost_monitor,
        sensory_engine,
        event_engine,
        orchestrator,
    )
