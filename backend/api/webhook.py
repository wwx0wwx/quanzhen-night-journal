from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from backend.api.deps import get_event_engine, get_orchestrator
from backend.engine.event_engine import EventEngine
from backend.engine.generation_orchestrator import GenerationOrchestrator
from backend.utils.response import error, success


router = APIRouter()


@router.post("/trigger")
async def trigger_webhook(
    request: Request,
    event_engine: EventEngine = Depends(get_event_engine),
    orchestrator: GenerationOrchestrator = Depends(get_orchestrator),
) -> object:
    payload = await request.json()
    raw_body = await request.body()
    event = await event_engine.handle_webhook(
        payload,
        auth_header=request.headers.get("Authorization"),
        raw_body=raw_body,
        signature_header=request.headers.get("X-Signature"),
    )
    if event is None:
        return error(2001, "Webhook 未通过鉴权、去重或冷却检查", status_code=401)
    task = await orchestrator.execute(event)
    return success({"event_id": event.id, "task_id": task.id, "task_status": task.status})
