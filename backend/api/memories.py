from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_memory_engine
from backend.api.serializers import memory_to_dict
from backend.database import get_session
from backend.engine.memory_engine import MemoryEngine
from backend.models import Memory
from backend.schemas.memory import MemoryCreate, MemorySearchRequest, MemoryUpdate
from backend.security.auth import get_current_user
from backend.utils.audit import log_audit
from backend.utils.response import error, paginated, success
from backend.utils.serde import json_dumps

router = APIRouter()


@router.get("")
async def list_memories(
    persona_id: int | None = None,
    level: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    stmt = select(Memory)
    count_stmt = select(func.count()).select_from(Memory)
    if persona_id is not None:
        stmt = stmt.where(Memory.persona_id == persona_id)
        count_stmt = count_stmt.where(Memory.persona_id == persona_id)
    if level:
        stmt = stmt.where(Memory.level == level)
        count_stmt = count_stmt.where(Memory.level == level)
    stmt = stmt.order_by(Memory.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = await db.scalars(stmt)
    total = await db.scalar(count_stmt) or 0
    return paginated([memory_to_dict(item) for item in rows], int(total), page, page_size)


@router.post("")
async def create_memory(
    payload: MemoryCreate,
    db: AsyncSession = Depends(get_session),
    engine: MemoryEngine = Depends(get_memory_engine),
    _user=Depends(get_current_user),
) -> object:
    memory = await engine.create_memory(payload)
    await log_audit(db, "user", "memory.create", "memory", str(memory.id))
    await db.commit()
    return success(memory_to_dict(memory))


@router.get("/stats")
async def memory_stats(
    engine: MemoryEngine = Depends(get_memory_engine),
    _user=Depends(get_current_user),
) -> object:
    return success(await engine.stats())


@router.get("/{memory_id}")
async def get_memory(
    memory_id: int,
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    memory = await db.get(Memory, memory_id)
    if memory is None:
        return error(1002, "记忆不存在", status_code=404)
    return success(memory_to_dict(memory))


@router.put("/{memory_id}")
async def update_memory(
    memory_id: int,
    payload: MemoryUpdate,
    db: AsyncSession = Depends(get_session),
    engine: MemoryEngine = Depends(get_memory_engine),
    _user=Depends(get_current_user),
) -> object:
    memory = await db.get(Memory, memory_id)
    if memory is None:
        return error(1002, "记忆不存在", status_code=404)
    data = payload.model_dump(exclude_none=True)
    for key, value in data.items():
        if key == "tags":
            setattr(memory, key, json_dumps(value))
        elif key == "is_core":
            setattr(memory, key, 1 if value else 0)
        else:
            setattr(memory, key, value)
    if "content" in data:
        await engine.embed_and_store(memory.id, memory.content)
    await log_audit(db, "user", "memory.update", "memory", str(memory.id))
    await db.commit()
    return success(memory_to_dict(memory))


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: int,
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    memory = await db.get(Memory, memory_id)
    if memory is None:
        return error(1002, "记忆不存在", status_code=404)
    await db.delete(memory)
    await log_audit(db, "user", "memory.delete", "memory", str(memory.id))
    await db.commit()
    return success({"deleted": True})


@router.post("/{memory_id}/promote")
async def promote_memory(
    memory_id: int,
    db: AsyncSession = Depends(get_session),
    engine: MemoryEngine = Depends(get_memory_engine),
    _user=Depends(get_current_user),
) -> object:
    memory = await engine.promote(memory_id)
    if memory is None:
        return error(1002, "记忆不存在", status_code=404)
    await log_audit(db, "user", "memory.promote", "memory", str(memory.id))
    await db.commit()
    return success(memory_to_dict(memory))


@router.post("/search")
async def search_memories(
    payload: MemorySearchRequest,
    engine: MemoryEngine = Depends(get_memory_engine),
    _user=Depends(get_current_user),
) -> object:
    hits = await engine.search(
        query=payload.query,
        persona_id=payload.persona_id,
        top_k=payload.top_k,
        level_filter=payload.level_filter,
    )
    return success([item.model_dump() for item in hits])
