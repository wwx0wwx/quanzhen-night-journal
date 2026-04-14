from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.engine.config_store import ConfigStore
from backend.models import Event
from backend.security.webhook_auth import verify_bearer, verify_hmac
from backend.utils.serde import json_dumps, json_loads
from backend.utils.time import utcnow, utcnow_iso


class EventEngine:
    def __init__(self, db: AsyncSession, config_store: ConfigStore):
        self.db = db
        self.config_store = config_store

    async def create_event(
        self,
        event_type: str,
        source: str,
        payload: dict[str, Any],
        semantic_hint: str = "",
    ) -> Event:
        event = Event(
            event_type=event_type,
            source=source,
            raw_payload=json_dumps(payload),
            normalized_semantic=semantic_hint or self._normalize(payload),
            auth_status="passed",
            dedup_key=None,
            cooldown_status="ready",
            created_at=utcnow_iso(),
            task_id=None,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def create_manual_event(self, source: str, payload: dict[str, Any], semantic_hint: str = "") -> Event:
        return await self.create_event("manual", source, payload, semantic_hint)

    async def create_scheduler_event(self, source: str, payload: dict[str, Any], semantic_hint: str = "") -> Event:
        return await self.create_event("scheduler", source, payload, semantic_hint)

    async def handle_webhook(
        self,
        payload: dict[str, Any],
        *,
        auth_header: str | None,
        raw_body: bytes,
        signature_header: str | None = None,
    ) -> Event | None:
        if not await self._verify_auth(auth_header, raw_body, signature_header):
            event = Event(
                event_type="webhook",
                source=payload.get("source", "webhook"),
                raw_payload=json_dumps(payload),
                normalized_semantic=self._normalize(payload),
                auth_status="failed",
                dedup_key=None,
                cooldown_status="ready",
                created_at=utcnow_iso(),
                task_id=None,
            )
            self.db.add(event)
            await self.db.flush()
            return None

        dedup_key = self._compute_dedup_key(payload)
        if await self._is_duplicate(dedup_key) or await self._is_cooling():
            return None

        event = Event(
            event_type="webhook",
            source=payload.get("source", "webhook"),
            raw_payload=json_dumps(payload),
            normalized_semantic=self._normalize(payload),
            auth_status="passed",
            dedup_key=dedup_key,
            cooldown_status="ready",
            created_at=utcnow_iso(),
            task_id=None,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def _verify_auth(
        self,
        auth_header: str | None,
        raw_body: bytes,
        signature_header: str | None,
    ) -> bool:
        mode = await self.config_store.get("webhook.auth_mode", "bearer")
        token = await self.config_store.get("webhook.auth_token", "")
        if not token:
            return False
        if mode == "hmac":
            return verify_hmac(signature_header, raw_body, token)
        return verify_bearer(auth_header, token)

    async def _is_duplicate(self, dedup_key: str) -> bool:
        row = await self.db.scalar(
            select(Event).where(
                Event.event_type == "webhook",
                Event.auth_status == "passed",
                Event.dedup_key == dedup_key,
            )
        )
        return row is not None

    async def _is_cooling(self) -> bool:
        cooldown_seconds = int(await self.config_store.get("webhook.cooldown_seconds", "1800") or 1800)
        latest = await self.db.scalar(
            select(Event)
            .where(
                Event.event_type == "webhook",
                Event.auth_status == "passed",
            )
            .order_by(desc(Event.created_at))
            .limit(1)
        )
        if latest is None:
            return False
        created = datetime.fromisoformat(latest.created_at.replace("Z", "+00:00"))
        return (utcnow() - created).total_seconds() < cooldown_seconds

    def _compute_dedup_key(self, payload: dict[str, Any]) -> str:
        return hashlib.sha256(json_dumps(payload).encode("utf-8")).hexdigest()

    def _normalize(self, payload: dict[str, Any]) -> str:
        pieces = []
        for key, value in payload.items():
            if isinstance(value, dict):
                inner = " ".join(f"{k}:{v}" for k, v in value.items())
                pieces.append(f"{key} {inner}")
            else:
                pieces.append(f"{key} {value}")
        return " | ".join(pieces)
