from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import delete, select

from backend.api.router import router as api_router
from backend.config import get_settings
from backend.database import close_database, get_sessionmaker, init_database
from backend.engine.config_store import ConfigStore
from backend.engine.folder_monitor_manager import FolderMonitorManager
from backend.engine.persona_engine import PersonaEngine
from backend.engine.site_runtime import SiteRuntimeManager
from backend.middleware.rate_limit import RateLimitMiddleware
from backend.models import Event, GenerationTask, Persona, PublicPageView
from backend.scheduler.jobs import ensure_seed_persona
from backend.scheduler.scheduler import setup_scheduler
from backend.security.encryption import ensure_encryptor
from backend.utils.audit import log_audit
from backend.utils.audit_catalog import ensure_audit_event_definitions
from backend.utils.legacy_import import import_legacy_assets
from backend.utils.metrics import METRICS
from backend.utils.response import error
from backend.utils.seed_posts import create_seed_posts
from backend.utils.time import utcnow_iso

logger = logging.getLogger(__name__)
scheduler = None
folder_monitor_manager = None

# Durable waiting states survive container restarts.
PRESERVE_ON_RESTART = frozenset({"waiting_human_signoff"})
# Queued tasks that never left the queue can be re-dispatched via their events.
REQUEUE_ON_RESTART = frozenset({"queued"})
TERMINAL_STATUSES = frozenset({"published", "failed", "circuit_open", "aborted", "draft_saved"})


async def _record_startup_action(
    db,
    action: str,
    detail: dict[str, object],
    *,
    severity: str = "info",
) -> None:
    logger.info("startup action=%s detail=%s severity=%s", action, detail, severity)
    await log_audit(db, "system", action, "system", "startup", detail, severity=severity)


async def _recover_interrupted_tasks(db) -> dict[str, list[int]]:
    """Classify non-terminal tasks after process restart.

    - waiting_human_signoff: keep (human still needs to act)
    - queued: mark failed then re-dispatch source event after boot
    - other in-flight: mark failed with container_restart
    """
    stuck_rows = await db.scalars(
        select(GenerationTask).where(GenerationTask.status.notin_(list(TERMINAL_STATUSES)))
    )
    stuck_tasks = list(stuck_rows)
    preserved: list[int] = []
    requeue_event_ids: list[int] = []
    failed: list[int] = []
    now = utcnow_iso()

    for task in stuck_tasks:
        if task.status in PRESERVE_ON_RESTART:
            preserved.append(task.id)
            continue

        event_id = task.event_id if task.status in REQUEUE_ON_RESTART else None
        task.status = "failed"
        task.error_code = "container_restart"
        task.error_message = "container_restart"
        task.finished_at = now
        failed.append(task.id)
        if event_id:
            requeue_event_ids.append(int(event_id))

    return {
        "preserved_task_ids": preserved,
        "failed_task_ids": failed,
        "requeue_event_ids": requeue_event_ids,
    }


async def _requeue_events(event_ids: list[int]) -> None:
    """Best-effort re-dispatch of events for tasks that were still queued at restart."""
    if not event_ids:
        return
    # De-dupe while preserving order.
    seen: set[int] = set()
    ordered: list[int] = []
    for event_id in event_ids:
        if event_id in seen:
            continue
        seen.add(event_id)
        ordered.append(event_id)

    from backend.scheduler.jobs import _runtime  # local import to avoid circulars at module load

    for event_id in ordered:
        try:
            async for (
                db,
                _config_store,
                persona_engine,
                _memory_engine,
                _qa_engine,
                _cost_monitor,
                _sensory_engine,
                _event_engine,
                orchestrator,
            ) in _runtime():
                event = await db.get(Event, event_id)
                if event is None:
                    logger.warning("restart requeue skipped missing event_id=%s", event_id)
                    break
                persona = await persona_engine.get_active_persona()
                task = await orchestrator.execute(event, persona=persona)
                METRICS.incr("tasks.restart_requeued")
                logger.info(
                    "restart requeued event_id=%s new_task_id=%s status=%s",
                    event_id,
                    task.id,
                    task.status,
                )
                break
        except Exception:  # noqa: BLE001
            logger.exception("restart requeue failed event_id=%s", event_id)
            METRICS.incr("tasks.restart_requeue_failures")


async def startup_self_check() -> dict[str, list[int]]:
    settings = get_settings()
    settings.validate_runtime()
    recovery: dict[str, list[int]] = {
        "preserved_task_ids": [],
        "failed_task_ids": [],
        "requeue_event_ids": [],
    }
    session_factory = get_sessionmaker()
    async with session_factory() as db:
        await ensure_audit_event_definitions(db)
        recovery = await _recover_interrupted_tasks(db)

        _, created_encryption_key = await ensure_encryptor(db)
        if created_encryption_key:
            await _record_startup_action(
                db,
                "system.ensure_encryption_key",
                {"created": True, "key": "system.encryption_key"},
                severity="warning",
            )

        had_default_persona = await db.scalar(select(Persona.id).where(Persona.is_default == 1))
        await ensure_seed_persona(db)
        if had_default_persona is None:
            default_persona = await db.scalar(select(Persona.id).where(Persona.is_default == 1))
            if default_persona is not None:
                await _record_startup_action(
                    db,
                    "system.ensure_seed_persona",
                    {"created": True, "persona_id": int(default_persona)},
                    severity="warning",
                )

        if settings.import_legacy_assets:
            legacy_result = await import_legacy_assets(db, settings)
            if legacy_result.get("posts") or legacy_result.get("memories"):
                await _record_startup_action(
                    db,
                    "system.import_legacy_assets",
                    legacy_result,
                    severity="warning",
                )

        default_persona = await db.scalar(select(Persona).where(Persona.is_default == 1))
        seed_post_count = await create_seed_posts(db, default_persona.id if default_persona else None)
        if seed_post_count:
            await _record_startup_action(
                db,
                "system.import_seed_posts",
                {"posts": seed_post_count},
            )
        config_store = ConfigStore(db)
        deprecated_keys = await config_store.purge_deprecated_keys()
        if deprecated_keys:
            await _record_startup_action(
                db,
                "system.purge_deprecated_config_keys",
                {"removed_keys": deprecated_keys},
                severity="warning",
            )
        runtime_status = await SiteRuntimeManager(config_store).apply()
        await _record_startup_action(
            db,
            "system.apply_site_runtime",
            {
                "domain": runtime_status.get("domain", ""),
                "enabled": bool(runtime_status.get("enabled")),
                "base_url": runtime_status.get("base_url", ""),
                "reason": runtime_status.get("reason", ""),
            },
        )
        repaired_personas = await PersonaEngine(db).repair_corrupted_personas()
        if recovery["failed_task_ids"] or recovery["preserved_task_ids"] or recovery["requeue_event_ids"]:
            await _record_startup_action(
                db,
                "system.restart_recovery",
                {
                    "failed_tasks": len(recovery["failed_task_ids"]),
                    "preserved_tasks": len(recovery["preserved_task_ids"]),
                    "requeue_events": len(recovery["requeue_event_ids"]),
                    "failed_task_ids": recovery["failed_task_ids"],
                    "preserved_task_ids": recovery["preserved_task_ids"],
                    "requeue_event_ids": recovery["requeue_event_ids"],
                },
                severity="warning",
            )
            METRICS.set_gauge("tasks.restart_failed", float(len(recovery["failed_task_ids"])))
            METRICS.set_gauge("tasks.restart_preserved", float(len(recovery["preserved_task_ids"])))
        if repaired_personas:
            logger.warning("startup repaired_corrupted_personas persona_ids=%s", repaired_personas)
            await log_audit(
                db,
                "system",
                "persona.repair_corrupted",
                "persona",
                ",".join(str(item) for item in repaired_personas),
                {"persona_ids": repaired_personas},
                severity="warning",
            )

        retention_cutoff = (datetime.now(UTC) - timedelta(days=90)).isoformat()
        purged = await db.execute(
            delete(PublicPageView).where(PublicPageView.created_at < retention_cutoff)
        )
        if purged.rowcount:
            logger.info("startup purged_stale_page_views count=%d", purged.rowcount)

        await db.commit()
    return recovery


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global folder_monitor_manager, scheduler
    get_settings().validate_runtime()
    await init_database()
    recovery = await startup_self_check()
    folder_monitor_manager = FolderMonitorManager(asyncio.get_running_loop())
    await folder_monitor_manager.start()
    _app.state.folder_monitor_manager = folder_monitor_manager
    scheduler = await setup_scheduler()
    _app.state.scheduler = scheduler
    METRICS.note_event("startup", "complete")
    # Re-dispatch queued work after the app is fully up.
    if recovery.get("requeue_event_ids"):
        asyncio.create_task(_requeue_events(list(recovery["requeue_event_ids"])))
    yield
    if folder_monitor_manager is not None:
        folder_monitor_manager.stop()
    if scheduler is not None:
        scheduler.shutdown(wait=True)
    await close_database()


app = FastAPI(
    title="全真夜记 Core",
    version=get_settings().app_version,
    lifespan=lifespan,
)
app.include_router(api_router, prefix="/api")
app.add_middleware(RateLimitMiddleware)

_settings = get_settings()
_cors_origins = [
    "http://localhost:5210",
    "http://127.0.0.1:5210",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
for origin in (_settings.cors_origins or "").split(","):
    origin = origin.strip()
    if origin and origin not in _cors_origins:
        _cors_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request, exc: HTTPException):
    code = 2001 if exc.status_code == 401 else 1001
    if exc.detail == "system_not_initialized":
        code = 3001
    return error(code, str(exc.detail), status_code=exc.status_code)


@app.get("/")
async def root():
    return {"name": "全真夜记 Core", "version": get_settings().app_version, "docs": "/docs"}
