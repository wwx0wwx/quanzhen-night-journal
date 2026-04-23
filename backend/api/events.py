from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.serializers import event_to_dict
from backend.database import get_session
from backend.models import Event
from backend.security.auth import get_current_user
from backend.utils.response import error, paginated, success

router = APIRouter()


@router.get("")
async def list_events(
    type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    stmt = select(Event)
    count_stmt = select(func.count()).select_from(Event)
    if type:
        stmt = stmt.where(Event.event_type == type)
        count_stmt = count_stmt.where(Event.event_type == type)
    stmt = stmt.order_by(Event.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = await db.scalars(stmt)
    total = await db.scalar(count_stmt) or 0
    return paginated([event_to_dict(item) for item in rows], int(total), page, page_size)


@router.get("/{event_id}")
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    event = await db.get(Event, event_id)
    if event is None:
        return error(1002, "事件不存在", status_code=404)
    return success(event_to_dict(event))
