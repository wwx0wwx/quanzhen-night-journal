from __future__ import annotations

from pydantic import BaseModel, Field

from backend.schemas.common import ORMModel


class MemoryBase(BaseModel):
    persona_id: int
    level: str = "L0"
    content: str
    summary: str = ""
    tags: list[str] = Field(default_factory=list)
    source: str = "hand_written"
    weight: float = 1.0
    time_range_start: str | None = None
    time_range_end: str | None = None
    review_status: str = "unreviewed"
    decay_strategy: str = "standard"
    is_core: bool = False


class MemoryCreate(MemoryBase):
    pass


class MemoryUpdate(BaseModel):
    content: str | None = None
    summary: str | None = None
    tags: list[str] | None = None
    weight: float | None = None
    review_status: str | None = None
    is_core: bool | None = None


class MemorySearchRequest(BaseModel):
    query: str
    persona_id: int
    top_k: int = 5
    level_filter: list[str] | None = None


class MemoryOut(ORMModel, MemoryBase):
    id: int
    created_at: str
    last_accessed_at: str | None = None


class MemoryHit(BaseModel):
    id: int
    level: str
    similarity: float
    weighted_score: float
    content: str
    summary: str
