from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.adapters.embedding_adapter import EmbeddingAdapter
from backend.adapters.llm_adapter import LLMAdapter
from backend.api.deps import get_config_store, get_site_runtime_manager
from backend.database import get_session
from backend.engine.config_store import SECRET_KEYS, ConfigStore
from backend.engine.site_runtime import SiteRuntimeManager
from backend.scheduler.scheduler import reload_scheduler
from backend.schemas.config import ConfigUpdateRequest, RevealSecretRequest, TestProviderRequest
from backend.security.auth import get_current_user
from backend.utils.audit import log_audit
from backend.utils.response import success

router = APIRouter()


@router.get("")
async def get_all_config(
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
    _user=Depends(get_current_user),
) -> object:
    return success(await config_store.as_public_dict())


@router.get("/{category}")
async def get_category_config(
    category: str,
    config_store: ConfigStore = Depends(get_config_store),
    _user=Depends(get_current_user),
) -> object:
    return success(await config_store.as_public_dict(category))


@router.put("")
async def update_config(
    payload: ConfigUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
    site_runtime: SiteRuntimeManager = Depends(get_site_runtime_manager),
    _user=Depends(get_current_user),
) -> object:
    changed_keys = {item.key for item in payload.items}
    await config_store.bulk_update([item.model_dump(exclude_unset=True) for item in payload.items])
    if changed_keys.intersection({"schedule.days_per_cycle", "schedule.posts_per_cycle"}):
        await config_store.set("schedule.cycle_anchor_date", date.today().isoformat(), category="schedule")
    runtime_status = await site_runtime.apply()
    await db.commit()
    if any(key.startswith("schedule.") for key in changed_keys):
        scheduler = getattr(request.app.state, "scheduler", None)
        if scheduler is not None:
            await reload_scheduler(scheduler)
    await log_audit(
        db,
        "user",
        "config.update",
        "config",
        detail={"count": len(payload.items), "changed_keys": sorted(changed_keys)},
    )
    await db.commit()
    return success({"updated": len(payload.items), "site_runtime": runtime_status})


@router.get("/status/domain")
async def domain_status(
    config_store: ConfigStore = Depends(get_config_store),
    _user=Depends(get_current_user),
) -> object:
    return success(
        {
            "domain": await config_store.get("site.domain", "") or "",
            "enabled": (await config_store.get("site.domain_enabled", "0")) == "1",
            "status": await config_store.get("site.domain_status", "disabled") or "disabled",
            "reason": await config_store.get("site.domain_reason", "") or "",
            "checked_at": await config_store.get("site.domain_checked_at", "") or "",
            "base_url": await config_store.get("hugo.base_url", "/") or "/",
        }
    )


@router.post("/reveal")
async def reveal_secret(
    payload: RevealSecretRequest,
    config_store: ConfigStore = Depends(get_config_store),
    _user=Depends(get_current_user),
) -> object:
    if payload.key not in SECRET_KEYS:
        raise HTTPException(status_code=400, detail="only secret keys can be revealed")
    value = await config_store.get(payload.key, default="", decrypt=True)
    return success({"key": payload.key, "value": value or ""})


@router.post("/test-llm")
async def test_llm(
    payload: TestProviderRequest,
    config_store: ConfigStore = Depends(get_config_store),
    _user=Depends(get_current_user),
) -> object:
    adapter = LLMAdapter()
    request_data = payload.model_dump()
    if request_data["api_key"] == "******":
        request_data["api_key"] = await config_store.get("llm.api_key", "") or ""
    return success(await adapter.test_connection(**request_data))


@router.post("/test-embedding")
async def test_embedding(
    payload: TestProviderRequest,
    config_store: ConfigStore = Depends(get_config_store),
    _user=Depends(get_current_user),
) -> object:
    adapter = EmbeddingAdapter()
    request_data = payload.model_dump()
    if request_data["api_key"] == "******":
        request_data["api_key"] = await config_store.get("embedding.api_key", "") or ""
    return success(await adapter.test_connection(**request_data))
