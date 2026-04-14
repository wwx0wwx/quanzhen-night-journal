from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session
from backend.models import AuditLog
from backend.security.auth import get_current_user
from backend.utils.serde import json_loads
from backend.utils.response import paginated


router = APIRouter()


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
    rows = await db.scalars(stmt)
    total = await db.scalar(count_stmt) or 0
    items = [
        {
            "id": row.id,
            "timestamp": row.timestamp,
            "actor": row.actor,
            "action": row.action,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "detail": json_loads(row.detail, {}),
            "ip_address": row.ip_address,
            "severity": row.severity,
        }
        for row in rows
    ]
    return paginated(items, int(total), page, page_size)
