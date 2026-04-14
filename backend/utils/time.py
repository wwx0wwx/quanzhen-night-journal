from __future__ import annotations

from datetime import datetime, timezone


UTC = timezone.utc


def utcnow() -> datetime:
    return datetime.now(UTC)


def utcnow_iso() -> str:
    return utcnow().replace(microsecond=0).isoformat()
