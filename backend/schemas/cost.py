from __future__ import annotations

from pydantic import BaseModel

from backend.schemas.common import ORMModel


class CostRecordOut(ORMModel):
    id: int
    task_id: int | None = None
    call_type: str
    model_id: str
    token_input: int
    token_output: int
    token_total: int
    cost_estimate: float
    currency: str
    created_at: str
    response_latency_ms: int


class BudgetStatus(BaseModel):
    remaining: float
    limit: float
    is_hibernating: bool
