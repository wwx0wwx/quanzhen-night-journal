from __future__ import annotations

import json
import shutil

import httpx
from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_config_store
from backend.config import get_settings
from backend.database import get_session
from backend.engine.config_store import ConfigStore
from backend.publisher.hugo_publisher import HugoPublisher
from backend.utils.response import success

router = APIRouter()


@router.get("")
async def health(
    request: Request,
    probe_external: bool = False,
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
) -> object:
    checks = await _collect_checks(request, db, config_store, probe_external=probe_external)
    return success({"status": _severity_from_checks(checks), "checks": checks})


@router.get("/ping")
async def ping() -> object:
    return success({"status": "ok"})


def _severity_from_checks(checks: dict[str, dict]) -> str:
    statuses = {item.get("status", "unknown") for item in checks.values()}
    if "error" in statuses:
        return "error"
    if "warning" in statuses:
        return "degraded"
    return "ok"


async def _provider_status(
    config_store: ConfigStore,
    prefix: str,
    *,
    require_api_key: bool = True,
    probe_external: bool = False,
) -> dict[str, object]:
    base_url_value = (await config_store.get(f"{prefix}.base_url", "")) or ""
    model_id_value = (await config_store.get(f"{prefix}.model_id", "")) or ""
    api_key_value = (await config_store.get(f"{prefix}.api_key", "")) if require_api_key else "configured"
    base_url = bool(base_url_value)
    model_id = bool(model_id_value)
    api_key = bool(api_key_value) if require_api_key else True
    missing = []
    if not base_url:
        missing.append("base_url")
    if not model_id:
        missing.append("model_id")
    if not api_key:
        missing.append("api_key")
    status = {
        "status": "ok" if not missing else "warning",
        "configured": not missing,
        "missing": missing,
    }
    if not missing and probe_external:
        status["reachability"] = await _probe_http_endpoint(base_url_value)
        if status["reachability"]["status"] == "error":
            status["status"] = "warning"
    else:
        status["reachability"] = {"status": "skipped" if not probe_external else "not_configured"}
    return status


def _read_build_status() -> dict[str, object]:
    publisher = HugoPublisher()
    if not publisher.settings.build_status_path.exists():
        return {"status": "warning", "detail": "build_status_missing"}

    try:
        payload = json.loads(publisher.settings.build_status_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "warning", "detail": "build_status_invalid_json"}

    status = payload.get("status", "unknown")
    if status == "ok":
        return {"status": "ok", "built_at": payload.get("built_at", "")}
    if status == "error":
        return {
            "status": "error",
            "detail": payload.get("error", "hugo_build_failed"),
            "built_at": payload.get("built_at", ""),
        }
    return {"status": "warning", "detail": "build_status_unknown"}


async def _probe_http_endpoint(base_url: str) -> dict[str, object]:
    url = base_url.rstrip("/") or base_url
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(3.0), follow_redirects=True) as client:
            response = await client.get(url)
        if response.status_code >= 500:
            return {"status": "error", "http_status": response.status_code}
        return {"status": "ok", "http_status": response.status_code}
    except httpx.RequestError as exc:
        return {"status": "error", "detail": exc.__class__.__name__}


async def _database_check(db: AsyncSession) -> dict[str, object]:
    await db.execute(text("SELECT 1"))
    row = await db.execute(text("PRAGMA encoding"))
    encoding = row.scalar() or "unknown"
    return {"status": "ok", "encoding": encoding}


def _disk_check() -> dict[str, object]:
    settings = get_settings()
    total, used, free = shutil.disk_usage(settings.data_dir)
    free_ratio = free / max(1, total)
    status = "ok" if free_ratio >= 0.03 or free >= 2 * 1024 * 1024 * 1024 else "warning"
    return {
        "status": status,
        "total_bytes": total,
        "used_bytes": used,
        "free_bytes": free,
        "free_ratio": round(free_ratio, 4),
    }


async def _collect_checks(
    request: Request,
    db: AsyncSession,
    config_store: ConfigStore,
    *,
    probe_external: bool,
) -> dict[str, dict]:
    database_status = await _database_check(db)

    scheduler = getattr(request.app.state, "scheduler", None)
    folder_monitor_manager = getattr(request.app.state, "folder_monitor_manager", None)
    publisher = HugoPublisher()

    initialized = (await config_store.get("system.initialized", "0")) == "1"
    site_title = bool(await config_store.get("site.title", ""))
    llm_status = await _provider_status(config_store, "llm", probe_external=probe_external)
    embedding_status = await _provider_status(config_store, "embedding", probe_external=probe_external)
    build_status = _read_build_status()
    publisher_ok = await publisher.health_check()
    domain_enabled = (await config_store.get("site.domain_enabled", "0")) == "1"

    return {
        "api": {"status": "ok"},
        "database": database_status,
        "disk": _disk_check(),
        "scheduler": {
            "status": "ok" if scheduler and getattr(scheduler, "running", False) else "warning",
            "running": bool(scheduler and getattr(scheduler, "running", False)),
            "job_count": len(scheduler.get_jobs()) if scheduler else 0,
        },
        "folder_monitor": {
            "status": "ok"
            if folder_monitor_manager and getattr(folder_monitor_manager, "_started", False)
            else "warning",
            "running": bool(folder_monitor_manager and getattr(folder_monitor_manager, "_started", False)),
        },
        "publisher": {
            "status": "ok" if publisher_ok else "warning",
            "target": "hugo",
        },
        "hugo_build": build_status,
        "setup": {
            "status": "ok" if initialized else "warning",
            "initialized": initialized,
            "site_title_ready": site_title,
        },
        "llm": llm_status,
        "embedding": embedding_status,
        "domain": {
            "status": "ok",
            "enabled": domain_enabled,
            "reason": await config_store.get("site.domain_reason", "") or "",
        },
    }


@router.get("/system")
async def system_health(
    request: Request,
    probe_external: bool = False,
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
) -> object:
    checks = await _collect_checks(request, db, config_store, probe_external=probe_external)

    return success(
        {
            "status": _severity_from_checks(checks),
            "checks": checks,
        }
    )
