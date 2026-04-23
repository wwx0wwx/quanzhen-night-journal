from __future__ import annotations

import logging
from typing import Any

import httpx

from backend.engine.config_store import ConfigStore
from backend.utils.time import utcnow_iso

logger = logging.getLogger(__name__)


class NotificationManager:
    def __init__(self, config_store: ConfigStore):
        self.config_store = config_store

    async def send(
        self,
        *,
        event_type: str,
        title: str,
        severity: str,
        detail: dict[str, Any],
    ) -> bool:
        enabled = (await self.config_store.get("notify.enabled", "0")) == "1"
        webhook_url = (await self.config_store.get("notify.webhook_url", "")) or ""
        bearer_token = (await self.config_store.get("notify.bearer_token", "")) or ""
        if not enabled or not webhook_url:
            return False

        headers = {"Content-Type": "application/json"}
        if bearer_token and bearer_token != "******":
            headers["Authorization"] = f"Bearer {bearer_token}"

        payload = {
            "event_type": event_type,
            "title": title,
            "severity": severity,
            "detail": detail,
            "sent_at": utcnow_iso(),
        }
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.post(webhook_url, json=payload, headers=headers)
                response.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            logger.warning("notification delivery failed event_type=%s error=%s", event_type, exc)
            return False
