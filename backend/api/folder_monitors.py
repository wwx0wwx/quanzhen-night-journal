from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session
from backend.models import FolderMonitor
from backend.security.auth import get_current_user
from backend.utils.audit import log_audit
from backend.utils.serde import json_dumps, json_loads
from backend.utils.response import success
from backend.utils.time import utcnow_iso


class FolderMonitorCreate(BaseModel):
    path: str = Field(..., min_length=1)
    file_types: list[str] = Field(default_factory=lambda: ["txt", "md"])


router = APIRouter()


@router.get("")
async def list_monitors(
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    rows = await db.scalars(select(FolderMonitor).order_by(FolderMonitor.id.desc()))
    return success(
        [
            {
                "id": row.id,
                "path": row.path,
                "is_active": bool(row.is_active),
                "file_types": json_loads(row.file_types, ["txt", "md"]),
                "created_at": row.created_at,
            }
            for row in rows
        ]
    )


@router.post("")
async def add_monitor(
    payload: FolderMonitorCreate,
    request: Request,
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    monitor = FolderMonitor(
        path=payload.path,
        is_active=1,
        file_types=json_dumps(payload.file_types),
        created_at=utcnow_iso(),
    )
    db.add(monitor)
    await db.flush()
    await log_audit(db, "user", "folder_monitor.create", "folder_monitor", str(monitor.id))
    await db.commit()
    manager = getattr(request.app.state, "folder_monitor_manager", None)
    if manager is not None:
        await manager.reload()
    return success({"id": monitor.id})


@router.delete("/{monitor_id}")
async def delete_monitor(
    monitor_id: int,
    request: Request,
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    monitor = await db.get(FolderMonitor, monitor_id)
    if monitor is not None:
        await db.delete(monitor)
        await log_audit(db, "user", "folder_monitor.delete", "folder_monitor", str(monitor_id))
        await db.commit()
    manager = getattr(request.app.state, "folder_monitor_manager", None)
    if manager is not None:
        await manager.reload()
    return success({"deleted": True})
