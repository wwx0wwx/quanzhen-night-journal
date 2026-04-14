from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_persona_engine, get_sensory_engine
from backend.api.serializers import sensory_to_dict
from backend.database import get_session
from backend.engine.persona_engine import PersonaEngine
from backend.engine.sensory_engine import SensoryEngine
from backend.security.auth import get_current_user
from backend.utils.serde import json_dumps, json_loads
from backend.utils.response import success


router = APIRouter()


@router.get("/current")
async def current_sensory(
    db: AsyncSession = Depends(get_session),
    sensory_engine: SensoryEngine = Depends(get_sensory_engine),
    persona_engine: PersonaEngine = Depends(get_persona_engine),
    _user=Depends(get_current_user),
) -> object:
    snapshot = await sensory_engine.sample()
    persona = await persona_engine.get_active_persona()
    if persona:
        snapshot.persona_id = persona.id
        snapshot.translated_text = persona_engine.translate_sensory(persona, json_loads(snapshot.tags, []))
        await db.commit()
    return success(sensory_to_dict(snapshot))


@router.get("/history")
async def sensory_history(
    hours: int = 24,
    sensory_engine: SensoryEngine = Depends(get_sensory_engine),
    _user=Depends(get_current_user),
) -> object:
    rows = await sensory_engine.history(hours=hours)
    return success([sensory_to_dict(item) for item in rows])


@router.get("/chart-data")
async def sensory_chart_data(
    hours: int = 24,
    sensory_engine: SensoryEngine = Depends(get_sensory_engine),
    _user=Depends(get_current_user),
) -> object:
    rows = await sensory_engine.history(hours=hours)
    items = [
        {
            "sampled_at": row.sampled_at,
            "cpu_percent": row.cpu_percent,
            "memory_percent": row.memory_percent,
            "load_average": row.load_average,
        }
        for row in rows
    ]
    return success(items)
