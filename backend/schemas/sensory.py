from __future__ import annotations

from pydantic import BaseModel

from backend.schemas.common import ORMModel


class SensoryOut(ORMModel):
    id: int
    source: str
    sampled_at: str
    cpu_percent: float | None = None
    memory_percent: float | None = None
    io_read_bytes: int | None = None
    io_write_bytes: int | None = None
    io_read_delta_bytes: int | None = None
    io_write_delta_bytes: int | None = None
    io_read_bytes_per_sec: float | None = None
    io_write_bytes_per_sec: float | None = None
    disk_usage_percent: float | None = None
    network_rx_bytes: int | None = None
    network_tx_bytes: int | None = None
    network_rx_delta_bytes: int | None = None
    network_tx_delta_bytes: int | None = None
    network_rx_bytes_per_sec: float | None = None
    network_tx_bytes_per_sec: float | None = None
    sample_interval_seconds: float | None = None
    load_average: float | None = None
    api_latency_ms: int | None = None
    tags: str
    translated_text: str
    persona_id: int | None = None
    is_in_blind_zone: int


class SensoryChartPoint(BaseModel):
    sampled_at: str
    cpu_percent: float | None = None
    memory_percent: float | None = None
    load_average: float | None = None
