from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import AuditLog


UTC = timezone.utc


async def log_audit(
    db: AsyncSession,
    actor: str,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    detail: dict[str, Any] | None = None,
    ip: str | None = None,
    severity: str = "info",
) -> AuditLog:
    entry = AuditLog(
        timestamp=datetime.now(UTC).replace(microsecond=0).isoformat(),
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=json.dumps(detail or {}, ensure_ascii=False),
        ip_address=ip,
        severity=severity,
    )
    db.add(entry)
    await db.flush()
    return entry
