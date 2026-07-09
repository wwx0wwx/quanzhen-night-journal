from __future__ import annotations

import asyncio

from backend.database import get_sessionmaker
from backend.main import _recover_interrupted_tasks
from backend.models import Event, GenerationTask
from backend.utils.time import utcnow_iso


def test_restart_preserves_human_signoff_and_fails_inflight(authed_client):
    async def seed() -> dict[str, int]:
        session_factory = get_sessionmaker()
        async with session_factory() as db:
            event = Event(
                event_type="manual",
                source="test",
                raw_payload="{}",
                normalized_semantic="restart test",
                auth_status="passed",
                dedup_key=None,
                cooldown_status="ready",
                created_at=utcnow_iso(),
                task_id=None,
            )
            db.add(event)
            await db.flush()

            waiting = GenerationTask(
                trigger_source="manual",
                event_id=event.id,
                persona_id=1,
                context_snapshot="{}",
                memory_hits="[]",
                sensory_snapshot_id=None,
                prompt_summary="{}",
                generated_content="draft",
                qa_result="{}",
                retry_count=0,
                max_retries=3,
                token_input=0,
                token_output=0,
                cost_estimate=0.0,
                status="waiting_human_signoff",
                cold_start=0,
                anti_perfection=0,
                queue_wait_ms=0,
                trace_json="[]",
                error_code=None,
                error_message=None,
                started_at=utcnow_iso(),
                finished_at=None,
                post_id=None,
            )
            generating = GenerationTask(
                trigger_source="manual",
                event_id=event.id,
                persona_id=1,
                context_snapshot="{}",
                memory_hits="[]",
                sensory_snapshot_id=None,
                prompt_summary="{}",
                generated_content=None,
                qa_result="{}",
                retry_count=0,
                max_retries=3,
                token_input=0,
                token_output=0,
                cost_estimate=0.0,
                status="generating",
                cold_start=0,
                anti_perfection=0,
                queue_wait_ms=0,
                trace_json="[]",
                error_code=None,
                error_message=None,
                started_at=utcnow_iso(),
                finished_at=None,
                post_id=None,
            )
            queued = GenerationTask(
                trigger_source="manual",
                event_id=event.id,
                persona_id=1,
                context_snapshot="{}",
                memory_hits="[]",
                sensory_snapshot_id=None,
                prompt_summary="{}",
                generated_content=None,
                qa_result="{}",
                retry_count=0,
                max_retries=3,
                token_input=0,
                token_output=0,
                cost_estimate=0.0,
                status="queued",
                cold_start=0,
                anti_perfection=0,
                queue_wait_ms=0,
                trace_json="[]",
                error_code=None,
                error_message=None,
                started_at=utcnow_iso(),
                finished_at=None,
                post_id=None,
            )
            db.add_all([waiting, generating, queued])
            await db.commit()
            return {
                "event_id": event.id,
                "waiting_id": waiting.id,
                "generating_id": generating.id,
                "queued_id": queued.id,
            }

    ids = asyncio.run(seed())

    async def recover() -> dict:
        session_factory = get_sessionmaker()
        async with session_factory() as db:
            result = await _recover_interrupted_tasks(db)
            await db.commit()
            waiting = await db.get(GenerationTask, ids["waiting_id"])
            generating = await db.get(GenerationTask, ids["generating_id"])
            queued = await db.get(GenerationTask, ids["queued_id"])
            return {
                "result": result,
                "waiting_status": waiting.status if waiting else None,
                "generating_status": generating.status if generating else None,
                "queued_status": queued.status if queued else None,
            }

    outcome = asyncio.run(recover())
    assert ids["waiting_id"] in outcome["result"]["preserved_task_ids"]
    assert ids["generating_id"] in outcome["result"]["failed_task_ids"]
    assert ids["queued_id"] in outcome["result"]["failed_task_ids"]
    assert ids["event_id"] in outcome["result"]["requeue_event_ids"]
    assert outcome["waiting_status"] == "waiting_human_signoff"
    assert outcome["generating_status"] == "failed"
    assert outcome["queued_status"] == "failed"
