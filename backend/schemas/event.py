from __future__ import annotations

from pydantic import BaseModel

from backend.schemas.common import ORMModel


class WebhookTriggerRequest(BaseModel):
    source: str
    payload: dict


class EventOut(ORMModel):
    id: int
    event_type: str
    source: str
    raw_payload: str
    normalized_semantic: str
    auth_status: str
    dedup_key: str | None = None
    cooldown_status: str
    created_at: str
    task_id: int | None = None
