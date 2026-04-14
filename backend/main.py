from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from backend.api.router import router as api_router
from backend.config import get_settings
from backend.database import close_database, get_sessionmaker, init_database
from backend.engine.config_store import ConfigStore
from backend.engine.folder_monitor_manager import FolderMonitorManager
from backend.engine.persona_engine import PersonaEngine
from backend.engine.site_runtime import SiteRuntimeManager
from backend.middleware.rate_limit import RateLimitMiddleware
from backend.models import GenerationTask, Persona, SystemConfig
from backend.scheduler.jobs import ensure_seed_persona
from backend.scheduler.scheduler import setup_scheduler
from backend.utils.audit import log_audit
from backend.utils.audit_catalog import ensure_audit_event_definitions
from backend.utils.legacy_import import import_legacy_assets
from backend.utils.response import error
from backend.utils.time import utcnow_iso


logger = logging.getLogger(__name__)
scheduler = None
folder_monitor_manager = None


async def _record_startup_action(
    db,
    action: str,
    detail: dict[str, object],
    *,
    severity: str = "info",
) -> None:
    logger.info("startup action=%s detail=%s severity=%s", action, detail, severity)
    await log_audit(db, "system", action, "system", "startup", detail, severity=severity)


async def startup_self_check() -> None:
    settings = get_settings()
    settings.validate_runtime()
    session_factory = get_sessionmaker()
    async with session_factory() as db:
        await ensure_audit_event_definitions(db)
        stuck_rows = await db.scalars(
            select(GenerationTask).where(
                GenerationTask.status.notin_(["published", "failed", "circuit_open", "aborted", "draft_saved"])
            )
        )
        stuck_tasks = list(stuck_rows)
        for task in stuck_tasks:
            task.status = "failed"
            task.error_code = "container_restart"
            task.error_message = "container_restart"
            task.finished_at = utcnow_iso()

        encryption_key = await db.get(SystemConfig, "system.encryption_key")
        if encryption_key is None:
            db.add(
                SystemConfig(
                    key="system.encryption_key",
                    value="",
                    encrypted=0,
                    category="system",
                    updated_at=utcnow_iso(),
                )
            )
            await _record_startup_action(
                db,
                "system.ensure_encryption_key",
                {"created": True, "key": "system.encryption_key"},
                severity="warning",
            )

        had_default_persona = await db.scalar(select(Persona.id).where(Persona.is_default == 1))
        await ensure_seed_persona()
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
        config_store = ConfigStore(db)
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
        if stuck_tasks:
            await _record_startup_action(
                db,
                "system.restart_recovery",
                {"recovered_tasks": len(stuck_tasks), "task_ids": [task.id for task in stuck_tasks]},
                severity="warning",
            )
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
        await db.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global folder_monitor_manager, scheduler
    get_settings().validate_runtime()
    await init_database()
    await startup_self_check()
    folder_monitor_manager = FolderMonitorManager(asyncio.get_running_loop())
    await folder_monitor_manager.start()
    _app.state.folder_monitor_manager = folder_monitor_manager
    scheduler = await setup_scheduler()
    _app.state.scheduler = scheduler
    yield
    if folder_monitor_manager is not None:
        folder_monitor_manager.stop()
    if scheduler is not None:
        scheduler.shutdown(wait=False)
    await close_database()


app = FastAPI(
    title="全真夜记 Core",
    version=get_settings().app_version,
    lifespan=lifespan,
)
app.include_router(api_router, prefix="/api")
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5210",
        "http://127.0.0.1:5210",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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
