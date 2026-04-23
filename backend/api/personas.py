from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_persona_engine
from backend.api.serializers import persona_to_dict
from backend.database import get_session
from backend.engine.persona_engine import PersonaEngine
from backend.models import Persona
from backend.schemas.persona import PersonaCreate, PersonaUpdate
from backend.security.auth import get_current_user
from backend.utils.audit import log_audit
from backend.utils.response import error, success

router = APIRouter()


@router.get("")
async def list_personas(
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    rows = await db.scalars(select(Persona).order_by(Persona.id.asc()))
    return success([persona_to_dict(item) for item in rows])


@router.post("")
async def create_persona(
    payload: PersonaCreate,
    db: AsyncSession = Depends(get_session),
    engine: PersonaEngine = Depends(get_persona_engine),
    _user=Depends(get_current_user),
) -> object:
    persona = await engine.create_persona(payload)
    await log_audit(db, "user", "persona.create", "persona", str(persona.id), {"name": persona.name})
    await db.commit()
    return success(persona_to_dict(persona))


@router.get("/{persona_id}")
async def get_persona(
    persona_id: int,
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    persona = await db.get(Persona, persona_id)
    if persona is None:
        return error(1002, "人格不存在", status_code=404)
    return success(persona_to_dict(persona))


@router.put("/{persona_id}")
async def update_persona(
    persona_id: int,
    payload: PersonaUpdate,
    db: AsyncSession = Depends(get_session),
    engine: PersonaEngine = Depends(get_persona_engine),
    _user=Depends(get_current_user),
) -> object:
    persona = await engine.update_persona(persona_id, payload)
    if persona is None:
        return error(1002, "人格不存在", status_code=404)
    await log_audit(db, "user", "persona.update", "persona", str(persona.id))
    await db.commit()
    return success(persona_to_dict(persona))


@router.delete("/{persona_id}")
async def delete_persona(
    persona_id: int,
    db: AsyncSession = Depends(get_session),
    engine: PersonaEngine = Depends(get_persona_engine),
    _user=Depends(get_current_user),
) -> object:
    deleted = await engine.delete_persona(persona_id)
    if not deleted:
        return error(1002, "人格不存在", status_code=404)
    await log_audit(db, "user", "persona.delete", "persona", str(persona_id))
    await db.commit()
    return success({"deleted": True})


@router.post("/{persona_id}/activate")
async def activate_persona(
    persona_id: int,
    db: AsyncSession = Depends(get_session),
    engine: PersonaEngine = Depends(get_persona_engine),
    _user=Depends(get_current_user),
) -> object:
    persona = await engine.set_default(persona_id)
    if persona is None:
        return error(1002, "人格不存在", status_code=404)
    await log_audit(db, "user", "persona.activate", "persona", str(persona.id))
    await db.commit()
    return success(persona_to_dict(persona))


@router.get("/{persona_id}/stability")
async def get_persona_stability(
    persona_id: int,
    engine: PersonaEngine = Depends(get_persona_engine),
    _user=Depends(get_current_user),
) -> object:
    return success({"persona_id": persona_id, "score": await engine.calculate_stability_score(persona_id)})
