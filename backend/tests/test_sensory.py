from __future__ import annotations

import asyncio
from collections import namedtuple
from datetime import datetime, timezone

from backend.database import get_sessionmaker
from backend.engine.config_store import ConfigStore
from backend.engine.sensory_engine import SensoryEngine
from backend.models import SensorySnapshot


DiskUsage = namedtuple("DiskUsage", ["total", "used", "free", "percent"])
NetCounters = namedtuple("NetCounters", ["bytes_sent", "bytes_recv"])
IoCounters = namedtuple("IoCounters", ["read_bytes", "write_bytes"])
VirtualMemory = namedtuple("VirtualMemory", ["percent"])


def test_sensory_snapshot_tracks_delta_and_rate_without_sticky_io_spike(monkeypatch, authed_client):
    disk_values = [DiskUsage(100, 40, 60, 40.0), DiskUsage(100, 40, 60, 40.0)]
    net_values = [NetCounters(2_000, 1_000), NetCounters(2_000, 1_000)]
    io_values = [IoCounters(9_000_000, 120_000_000), IoCounters(9_000_000, 120_000_000)]
    sampled_at_values = iter(
        [
            "2026-04-15T21:00:00+00:00",
            "2026-04-15T21:01:00+00:00",
        ]
    )

    monkeypatch.setattr("backend.engine.sensory_engine.psutil.disk_usage", lambda _path: disk_values.pop(0))
    monkeypatch.setattr("backend.engine.sensory_engine.psutil.net_io_counters", lambda: net_values.pop(0))
    monkeypatch.setattr("backend.engine.sensory_engine.psutil.disk_io_counters", lambda: io_values.pop(0))
    monkeypatch.setattr("backend.engine.sensory_engine.psutil.cpu_percent", lambda interval=0.1: 3.0)
    monkeypatch.setattr("backend.engine.sensory_engine.psutil.virtual_memory", lambda: VirtualMemory(percent=28.0))
    monkeypatch.setattr("backend.engine.sensory_engine.os.getloadavg", lambda: (0.2, 0.1, 0.1))
    monkeypatch.setattr("backend.engine.sensory_engine.utcnow_iso", lambda: next(sampled_at_values))

    async def exercise() -> None:
        session_factory = get_sessionmaker()
        async with session_factory() as db:
            engine = SensoryEngine(db, ConfigStore(db))
            first = await engine.sample()
            second = await engine.sample()
            await db.commit()

            assert first.sample_interval_seconds is None
            assert second.sample_interval_seconds == 60.0
            assert second.io_write_delta_bytes == 0
            assert second.io_write_bytes_per_sec == 0.0
            assert second.network_rx_delta_bytes == 0
            assert second.network_rx_bytes_per_sec == 0.0
            assert "io_spike" not in second.tags

    asyncio.run(exercise())


def test_sensory_history_filters_by_hours(monkeypatch, authed_client):
    monkeypatch.setattr(
        "backend.engine.sensory_engine.utcnow",
        lambda: datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc),
    )

    async def exercise() -> None:
        session_factory = get_sessionmaker()
        async with session_factory() as db:
            db.add_all(
                [
                    SensorySnapshot(
                        source="container",
                        sampled_at="2026-04-19T10:00:00+00:00",
                        cpu_percent=10.0,
                        memory_percent=20.0,
                        tags="[]",
                        translated_text="",
                        persona_id=None,
                        is_in_blind_zone=0,
                    ),
                    SensorySnapshot(
                        source="container",
                        sampled_at="2026-04-18T08:00:00+00:00",
                        cpu_percent=11.0,
                        memory_percent=21.0,
                        tags="[]",
                        translated_text="",
                        persona_id=None,
                        is_in_blind_zone=0,
                    ),
                ]
            )
            await db.commit()

            engine = SensoryEngine(db, ConfigStore(db))
            rows = await engine.history(hours=24, limit=20)

            assert len(rows) == 1
            assert rows[0].sampled_at == "2026-04-19T10:00:00+00:00"

    asyncio.run(exercise())
