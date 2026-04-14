from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_config_store, get_persona_engine, get_site_runtime_manager
from backend.api.serializers import persona_to_dict
from backend.database import get_session
from backend.engine.config_store import ConfigStore
from backend.engine.persona_engine import PersonaEngine
from backend.engine.site_runtime import SiteRuntimeManager
from backend.models import Persona, User
from backend.schemas.auth import SetupCompleteRequest
from backend.security.auth import hash_password, is_system_initialized
from backend.utils.audit import log_audit
from backend.utils.default_persona import build_default_quanzhen_persona
from backend.utils.response import error, success


router = APIRouter()


@router.get("/status")
async def setup_status(
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
) -> object:
    admin = await db.scalar(select(User).where(User.username == "admin"))
    default_persona = await db.scalar(select(Persona).where(Persona.is_default == 1))
    return success(
        {
            "system_initialized": (await config_store.get("system.initialized", "0")) == "1",
            "admin_initialized": bool(admin.is_initialized) if admin else False,
            "has_default_persona": default_persona is not None,
        }
    )


@router.post("/complete")
async def setup_complete(
    payload: SetupCompleteRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
    persona_engine: PersonaEngine = Depends(get_persona_engine),
    site_runtime: SiteRuntimeManager = Depends(get_site_runtime_manager),
) -> object:
    admin = await db.scalar(select(User).where(User.username == "admin"))
    if admin is None:
        return error(1002, "管理员账户不存在", status_code=404)
    if await is_system_initialized(db):
        return error(3003, "系统已完成初始化，禁止再次执行初始化", status_code=403)

    admin.password_hash = hash_password(payload.new_password)
    admin.is_initialized = 1

    await config_store.set("site.title", payload.site_title, category="site")
    await config_store.set("site.subtitle", payload.site_subtitle, category="site")
    await config_store.set("site.domain", payload.site_domain, category="site")
    await config_store.set("llm.base_url", payload.llm_base_url, category="llm")
    await config_store.set("llm.api_key", payload.llm_api_key, category="llm", encrypted=True)
    await config_store.set("llm.model_id", payload.llm_model_id, category="llm")
    await config_store.set("embedding.base_url", payload.embedding_base_url, category="embedding")
    await config_store.set("embedding.api_key", payload.embedding_api_key, category="embedding", encrypted=True)
    await config_store.set("embedding.model_id", payload.embedding_model_id, category="embedding")
    await config_store.set("system.initialized", "1", category="system")

    default_persona = await db.scalar(select(Persona).where(Persona.is_default == 1))
    if default_persona is None:
        default_persona = await persona_engine.create_persona(build_default_quanzhen_persona())

    runtime_status = await site_runtime.apply()
    await log_audit(
        db,
        "user",
        "setup.complete",
        "system",
        "1",
        {"site_title": payload.site_title},
        ip=request.client.host if request.client else None,
    )
    await db.commit()
    return success(
        {
            "system_initialized": True,
            "default_persona": persona_to_dict(default_persona),
            "site_runtime": runtime_status,
        }
    )
