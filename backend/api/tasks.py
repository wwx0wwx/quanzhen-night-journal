from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_event_engine, get_orchestrator, get_persona_engine
from backend.api.serializers import task_to_dict
from backend.database import get_session
from backend.engine.event_engine import EventEngine
from backend.engine.generation_orchestrator import GenerationOrchestrator, InvalidTransition
from backend.engine.persona_engine import PersonaEngine
from backend.models import GenerationTask, Persona, Post
from backend.schemas.task import TaskApproveRequest, TaskTriggerRequest
from backend.security.auth import get_current_user
from backend.utils.response import error, paginated, success

router = APIRouter()


async def _build_post_map(db: AsyncSession, post_ids: list[int]) -> dict[int, Post]:
    if not post_ids:
        return {}
    rows = await db.scalars(select(Post).where(Post.id.in_(post_ids)))
    return {row.id: row for row in rows}


@router.get("")
async def list_tasks(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    stmt = select(GenerationTask)
    count_stmt = select(func.count()).select_from(GenerationTask)
    if status:
        stmt = stmt.where(GenerationTask.status == status)
        count_stmt = count_stmt.where(GenerationTask.status == status)
    stmt = stmt.order_by(GenerationTask.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = list(await db.scalars(stmt))
    total = await db.scalar(count_stmt) or 0
    post_map = await _build_post_map(db, [task.post_id for task in rows if task.post_id])
    items = [task_to_dict(task, post_map.get(task.post_id)) for task in rows]
    return paginated(items, int(total), page, page_size)


@router.get("/{task_id}")
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_session),
    orchestrator: GenerationOrchestrator = Depends(get_orchestrator),
    _user=Depends(get_current_user),
) -> object:
    task = await db.get(GenerationTask, task_id)
    if task is None:
        return error(1002, "任务不存在", status_code=404)
    post = await db.get(Post, task.post_id) if task.post_id else None
    data = task_to_dict(task, post)
    data["trace"] = await orchestrator.get_trace(task)
    return success(data)


@router.post("/trigger")
async def trigger_task(
    payload: TaskTriggerRequest,
    event_engine: EventEngine = Depends(get_event_engine),
    orchestrator: GenerationOrchestrator = Depends(get_orchestrator),
    persona_engine: PersonaEngine = Depends(get_persona_engine),
    _user=Depends(get_current_user),
) -> object:
    event = await event_engine.create_manual_event(
        source="manual",
        payload=payload.payload,
        semantic_hint=payload.semantic_hint,
    )
    persona = await persona_engine.get_active_persona()
    if payload.persona_id:
        persona = await orchestrator.db.get(Persona, payload.persona_id)
    task = await orchestrator.execute(event, persona=persona)
    return success({"id": task.id, "status": task.status, "post_id": task.post_id})


@router.post("/{task_id}/abort")
async def abort_task(
    task_id: int,
    orchestrator: GenerationOrchestrator = Depends(get_orchestrator),
    _user=Depends(get_current_user),
) -> object:
    task = await orchestrator.abort_task(task_id)
    if task is None:
        return error(1002, "任务不存在", status_code=404)
    return success({"id": task.id, "status": task.status})


@router.post("/{task_id}/approve")
async def approve_task(
    task_id: int,
    payload: TaskApproveRequest,
    orchestrator: GenerationOrchestrator = Depends(get_orchestrator),
    _user=Depends(get_current_user),
) -> object:
    current = await orchestrator.db.get(GenerationTask, task_id)
    if current is None:
        return error(1002, "任务不存在", status_code=404)
    if current.status != "waiting_human_signoff":
        return error(1001, "任务当前状态不允许人工签发", status_code=409)
    try:
        task = await orchestrator.approve_task(task_id, publish_immediately=payload.publish_immediately)
    except InvalidTransition:
        return error(1001, "任务当前状态不允许人工签发", status_code=409)
    if task is None:
        return error(1002, "任务不存在", status_code=404)
    return success({"id": task.id, "status": task.status, "post_id": task.post_id})


@router.get("/{task_id}/trace")
async def task_trace(
    task_id: int,
    db: AsyncSession = Depends(get_session),
    orchestrator: GenerationOrchestrator = Depends(get_orchestrator),
    _user=Depends(get_current_user),
) -> object:
    task = await db.get(GenerationTask, task_id)
    if task is None:
        return error(1002, "任务不存在", status_code=404)
    return success(await orchestrator.get_trace(task))
