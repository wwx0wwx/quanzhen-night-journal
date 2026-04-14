from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session
from backend.models import AuditLog, Event, GenerationTask
from backend.security.auth import get_current_user
from backend.utils.serde import json_loads
from backend.utils.response import paginated


router = APIRouter()


def _parse_int(value: object) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(str(value))
    except (TypeError, ValueError):
        return None


async def _load_processed_events(
    db: AsyncSession,
    rows: list[AuditLog],
) -> tuple[dict[int, str], dict[int, str]]:
    task_ids: set[int] = set()
    event_ids: set[int] = set()

    for row in rows:
        detail = json_loads(row.detail, {})
        if row.target_type == "task":
            task_id = _parse_int(row.target_id)
            if task_id is not None:
                task_ids.add(task_id)
        if row.target_type == "event":
            event_id = _parse_int(row.target_id)
            if event_id is not None:
                event_ids.add(event_id)
        if isinstance(detail, dict):
            task_id = _parse_int(detail.get("task_id"))
            event_id = _parse_int(detail.get("event_id"))
            if task_id is not None:
                task_ids.add(task_id)
            if event_id is not None:
                event_ids.add(event_id)

    task_event_map: dict[int, str] = {}
    if task_ids:
        task_rows = await db.execute(
            select(GenerationTask.id, Event.normalized_semantic)
            .outerjoin(Event, Event.id == GenerationTask.event_id)
            .where(GenerationTask.id.in_(task_ids))
        )
        task_event_map = {
            task_id: (normalized_semantic or "")
            for task_id, normalized_semantic in task_rows.all()
        }

    event_map: dict[int, str] = {}
    if event_ids:
        event_rows = await db.execute(
            select(Event.id, Event.normalized_semantic).where(Event.id.in_(event_ids))
        )
        event_map = {
            event_id: (normalized_semantic or "")
            for event_id, normalized_semantic in event_rows.all()
        }

    return task_event_map, event_map


def _resolve_processed_event(
    row: AuditLog,
    detail: object,
    task_event_map: dict[int, str],
    event_map: dict[int, str],
) -> str:
    if row.target_type == "task":
        task_id = _parse_int(row.target_id)
        if task_id is not None and task_event_map.get(task_id):
            return task_event_map[task_id]

    if row.target_type == "event":
        event_id = _parse_int(row.target_id)
        if event_id is not None and event_map.get(event_id):
            return event_map[event_id]

    if isinstance(detail, dict):
        task_id = _parse_int(detail.get("task_id"))
        if task_id is not None and task_event_map.get(task_id):
            return task_event_map[task_id]

        event_id = _parse_int(detail.get("event_id"))
        if event_id is not None and event_map.get(event_id):
            return event_map[event_id]

    return ""


@router.get("")
async def list_audit_logs(
    severity: str | None = None,
    action: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    stmt = select(AuditLog)
    count_stmt = select(func.count()).select_from(AuditLog)
    if severity:
        stmt = stmt.where(AuditLog.severity == severity)
        count_stmt = count_stmt.where(AuditLog.severity == severity)
    if action:
        stmt = stmt.where(AuditLog.action == action)
        count_stmt = count_stmt.where(AuditLog.action == action)
    stmt = stmt.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.scalars(stmt)).all()
    total = await db.scalar(count_stmt) or 0
    task_event_map, event_map = await _load_processed_events(db, rows)
    items = [
        {
            "id": row.id,
            "timestamp": row.timestamp,
            "actor": row.actor,
            "action": row.action,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "detail": detail,
            "ip_address": row.ip_address,
            "severity": row.severity,
            "processed_event": _resolve_processed_event(row, detail, task_event_map, event_map),
        }
        for row in rows
        for detail in [json_loads(row.detail, {})]
    ]
    return paginated(items, int(total), page, page_size)
