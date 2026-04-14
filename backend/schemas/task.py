from __future__ import annotations

from pydantic import BaseModel, Field

from backend.schemas.common import ORMModel


class TaskTriggerRequest(BaseModel):
    trigger_source: str = "manual"
    persona_id: int | None = None
    semantic_hint: str = ""
    payload: dict = Field(default_factory=dict)


class TaskApproveRequest(BaseModel):
    publish_immediately: bool = True


class TaskOut(ORMModel):
    id: int
    trigger_source: str
    event_id: int | None = None
    persona_id: int
    context_snapshot: str
    memory_hits: str
    sensory_snapshot_id: int | None = None
    prompt_summary: str
    generated_content: str | None = None
    qa_result: str
    retry_count: int
    max_retries: int
    token_input: int
    token_output: int
    cost_estimate: float
    status: str
    cold_start: int
    anti_perfection: int
    queue_wait_ms: int = 0
    trace_json: str = "[]"
    error_code: str | None = None
    error_message: str | None = None
    started_at: str
    finished_at: str | None = None
    post_id: int | None = None
