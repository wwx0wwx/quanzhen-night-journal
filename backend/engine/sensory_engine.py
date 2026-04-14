from __future__ import annotations

import os
from datetime import datetime

import psutil
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.engine.config_store import ConfigStore
from backend.models import Post, SensorySnapshot
from backend.utils.serde import json_dumps, json_loads
from backend.utils.time import utcnow, utcnow_iso


class SensoryEngine:
    LABEL_RULES = [
        ("high_cpu", lambda s, t: s.cpu_percent is not None and s.cpu_percent > t["cpu"]),
        ("memory_pressure", lambda s, t: s.memory_percent is not None and s.memory_percent > t["mem"]),
        ("memory_critical", lambda s, t: s.memory_percent is not None and s.memory_percent > 95),
        ("io_spike", lambda s, t: s.io_write_bytes is not None and s.io_write_bytes > 100_000_000),
        ("disk_warning", lambda s, t: s.disk_usage_percent is not None and s.disk_usage_percent > 90),
        ("network_heavy", lambda s, t: s.network_rx_bytes is not None and s.network_rx_bytes > 50_000_000),
        ("api_slow", lambda s, t: s.api_latency_ms is not None and s.api_latency_ms > 3000),
    ]

    def __init__(self, db: AsyncSession, config_store: ConfigStore):
        self.db = db
        self.config_store = config_store

    async def sample(self) -> SensorySnapshot:
        disk = psutil.disk_usage(str(os.getcwd()))
        net = psutil.net_io_counters()
        io = psutil.disk_io_counters()
        try:
            load = os.getloadavg()[0]
        except (AttributeError, OSError):
            load = None

        snapshot = SensorySnapshot(
            source=await self.config_store.get("sensory.source_mode", "container") or "container",
            sampled_at=utcnow_iso(),
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=psutil.virtual_memory().percent,
            io_read_bytes=io.read_bytes if io else None,
            io_write_bytes=io.write_bytes if io else None,
            disk_usage_percent=disk.percent,
            network_rx_bytes=net.bytes_recv,
            network_tx_bytes=net.bytes_sent,
            load_average=load,
            api_latency_ms=None,
            tags="[]",
            translated_text="",
            persona_id=None,
            is_in_blind_zone=0,
        )
        snapshot.tags = json_dumps(await self._apply_labels(snapshot))
        snapshot.is_in_blind_zone = 1 if await self._check_blind_zone() else 0
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot

    async def history(self, hours: int = 24, limit: int = 200) -> list[SensorySnapshot]:
        rows = await self.db.scalars(
            select(SensorySnapshot).order_by(desc(SensorySnapshot.sampled_at)).limit(limit)
        )
        return list(rows)

    async def _apply_labels(self, snapshot: SensorySnapshot) -> list[str]:
        thresholds = {
            "cpu": int(await self.config_store.get("sensory.cpu_high_threshold", "80") or 80),
            "mem": int(await self.config_store.get("sensory.mem_high_threshold", "85") or 85),
        }
        tags = [name for name, rule in self.LABEL_RULES if rule(snapshot, thresholds)]
        return tags or ["normal"]

    async def _check_blind_zone(self) -> bool:
        blind_minutes = int(await self.config_store.get("sensory.blind_zone_minutes", "30") or 30)
        post = await self.db.scalar(
            select(Post).where(Post.published_at.is_not(None)).order_by(desc(Post.published_at)).limit(1)
        )
        if post is None or not post.published_at:
            return False
        published = datetime.fromisoformat(post.published_at.replace("Z", "+00:00"))
        return abs((utcnow() - published).total_seconds()) <= blind_minutes * 60
