from __future__ import annotations

from datetime import UTC

from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_encryptor
from backend.database import get_sessionmaker
from backend.engine.config_store import ConfigStore
from backend.engine.ghost_manager import GhostManager
from backend.engine.notification_manager import NotificationManager
from backend.engine.persona_engine import PersonaEngine
from backend.engine.runtime_factory import build_generation_runtime
from backend.models import AuditLog
from backend.utils.audit import log_audit
from backend.utils.default_persona import (
    apply_default_persona_update,
    build_default_persona,
    is_legacy_default_persona,
)
from backend.utils.time import utcnow_iso


async def _runtime():
    session_factory = get_sessionmaker()
    async with session_factory() as db:
        encryptor = await get_encryptor(db)
        (
            config_store,
            persona_engine,
            memory_engine,
            qa_engine,
            cost_monitor,
            sensory_engine,
            event_engine,
            orchestrator,
        ) = build_generation_runtime(db, encryptor)
        yield (
            db,
            config_store,
            persona_engine,
            memory_engine,
            qa_engine,
            cost_monitor,
            sensory_engine,
            event_engine,
            orchestrator,
        )


async def _ensure_seed_persona_in_session(db: AsyncSession, *, commit: bool) -> None:
    persona_engine = PersonaEngine(db)
    persona = await persona_engine.get_active_persona()
    changed = False

    if persona is None:
        await persona_engine.create_persona(build_default_persona())
        changed = True
    elif is_legacy_default_persona(persona):
        apply_default_persona_update(persona)
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
    async for (
        _db,
        config_store,
        persona_engine,
        _memory_engine,
        _qa,
        _cost,
        _sensory,
        event_engine,
        orchestrator,
    ) in _runtime():
        initialized = await config_store.get("system.initialized", "0")
        if initialized != "1":
            return
        slot_time = scheduled_for or utcnow_iso()
        event = await event_engine.create_scheduler_event(
            source="scheduler",
            payload={
                "scheduled_at": utcnow_iso(),
                "scheduled_for": slot_time,
                "slot_index": slot_index,
            },
            semantic_hint=(
                f"定时发文任务触发（{slot_time}）"
                if slot_index == 0
                else f"定时补发任务触发 #{slot_index + 1}（{slot_time}）"
            ),
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


async def audit_cleanup_job(*, retention_days: int = 90) -> None:
    from datetime import datetime, timedelta

    from sqlalchemy import delete

    cutoff = (datetime.now(UTC) - timedelta(days=retention_days)).isoformat()
    session_factory = get_sessionmaker()
    async with session_factory() as db:
        await db.execute(delete(AuditLog).where(AuditLog.timestamp < cutoff))
        await db.commit()


async def run_auto_database_backup() -> None:
    from backend.config import get_settings

    session_factory = get_sessionmaker()
    async with session_factory() as db:
        encryptor = await get_encryptor(db)
        config_store = ConfigStore(db, encryptor)
        if (await config_store.get("backup.auto_enabled", "0")) != "1":
            return
        try:
            keep_count = int(await config_store.get("backup.keep_count", "7") or "7")
        except ValueError:
            keep_count = 7
        keep_count = max(1, min(keep_count, 30))
        settings = get_settings()
        manager = GhostManager(db, config_store, settings.ghost_path, settings.database_path.parent / "backups")
        try:
            path = await manager.backup_database(settings.database_path, automatic=True)
            deleted = await manager.prune_auto_database_backups(keep_count)
            await config_store.set("backup.last_auto_at", utcnow_iso(), category="backup")
            await config_store.set("backup.last_auto_ok", "1", category="backup")
            await config_store.set("backup.last_auto_filename", path.name, category="backup")
            await log_audit(
                db,
                "system",
                "backup.auto",
                "backup",
                path.name,
                {"keep_count": keep_count, "deleted": [item.name for item in deleted]},
            )
        except Exception as exc:  # noqa: BLE001
            await config_store.set("backup.last_auto_at", utcnow_iso(), category="backup")
            await config_store.set("backup.last_auto_ok", "0", category="backup")
            await log_audit(
                db,
                "system",
                "backup.auto_failed",
                "backup",
                "database",
                {"error": str(exc)},
                severity="error",
            )
            await NotificationManager(config_store).send(
                event_type="backup.auto_failed",
                title="Automatic database backup failed",
                severity="error",
                detail={"error": str(exc)},
            )
            raise
        finally:
            await db.commit()
