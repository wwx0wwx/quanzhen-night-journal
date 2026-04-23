from __future__ import annotations

import os
from datetime import datetime, timedelta

import psutil
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.engine.config_store import ConfigStore
from backend.models import Post, SensorySnapshot
from backend.utils.serde import json_dumps
from backend.utils.time import utcnow, utcnow_iso


class SensoryEngine:
    LABEL_RULES = [
        ("high_cpu", lambda s, t: s.cpu_percent is not None and s.cpu_percent > t["cpu"]),
        ("memory_pressure", lambda s, t: s.memory_percent is not None and s.memory_percent > t["mem"]),
        ("memory_critical", lambda s, t: s.memory_percent is not None and s.memory_percent > 95),
        (
            "io_spike",
            lambda s, t: (
                s.io_write_bytes_per_sec is not None and s.io_write_bytes_per_sec > t["io_write_bytes_per_sec"]
            ),
        ),
        ("disk_warning", lambda s, t: s.disk_usage_percent is not None and s.disk_usage_percent > 90),
        (
            "network_heavy",
            lambda s, t: (
                s.network_rx_bytes_per_sec is not None and s.network_rx_bytes_per_sec > t["network_rx_bytes_per_sec"]
            ),
        ),
        ("api_slow", lambda s, t: s.api_latency_ms is not None and s.api_latency_ms > 3000),
    ]

    def __init__(self, db: AsyncSession, config_store: ConfigStore):
        self.db = db
        self.config_store = config_store

    async def sample(self) -> SensorySnapshot:
        disk = psutil.disk_usage(str(os.getcwd()))
        net = psutil.net_io_counters()
        io = psutil.disk_io_counters()
        previous = await self._latest_snapshot()
        try:
            load = os.getloadavg()[0]
        except (AttributeError, OSError):
            load = None
        now_iso = utcnow_iso()
        interval_seconds, deltas = self._compute_deltas(previous, now_iso, io, net)

        snapshot = SensorySnapshot(
            source=await self.config_store.get("sensory.source_mode", "container") or "container",
            sampled_at=now_iso,
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=psutil.virtual_memory().percent,
            io_read_bytes=io.read_bytes if io else None,
            io_write_bytes=io.write_bytes if io else None,
            io_read_delta_bytes=deltas["io_read_delta_bytes"],
            io_write_delta_bytes=deltas["io_write_delta_bytes"],
            io_read_bytes_per_sec=deltas["io_read_bytes_per_sec"],
            io_write_bytes_per_sec=deltas["io_write_bytes_per_sec"],
            disk_usage_percent=disk.percent,
            network_rx_bytes=net.bytes_recv,
            network_tx_bytes=net.bytes_sent,
            network_rx_delta_bytes=deltas["network_rx_delta_bytes"],
            network_tx_delta_bytes=deltas["network_tx_delta_bytes"],
            network_rx_bytes_per_sec=deltas["network_rx_bytes_per_sec"],
            network_tx_bytes_per_sec=deltas["network_tx_bytes_per_sec"],
            sample_interval_seconds=interval_seconds,
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
        cutoff = (utcnow() - timedelta(hours=max(hours, 0))).isoformat()
        rows = await self.db.scalars(
            select(SensorySnapshot)
            .where(SensorySnapshot.sampled_at >= cutoff)
            .order_by(desc(SensorySnapshot.sampled_at))
            .limit(limit)
        )
        return list(rows)

    async def _apply_labels(self, snapshot: SensorySnapshot) -> list[str]:
        thresholds = {
            "cpu": int(await self.config_store.get("sensory.cpu_high_threshold", "80") or 80),
            "mem": int(await self.config_store.get("sensory.mem_high_threshold", "85") or 85),
            "io_write_bytes_per_sec": int(await self.config_store.get("sensory.io_high_threshold", "70") or 70)
            * 1024
            * 1024,
            "network_rx_bytes_per_sec": 50 * 1024 * 1024,
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

    async def _latest_snapshot(self) -> SensorySnapshot | None:
        rows = await self.db.scalars(select(SensorySnapshot).order_by(desc(SensorySnapshot.sampled_at)).limit(1))
        return rows.first()

    def _compute_deltas(
        self,
        previous: SensorySnapshot | None,
        current_sampled_at: str,
        io,
        net,
    ) -> tuple[float | None, dict[str, int | float | None]]:
        empty = {
            "io_read_delta_bytes": None,
            "io_write_delta_bytes": None,
            "io_read_bytes_per_sec": None,
            "io_write_bytes_per_sec": None,
            "network_rx_delta_bytes": None,
            "network_tx_delta_bytes": None,
            "network_rx_bytes_per_sec": None,
            "network_tx_bytes_per_sec": None,
        }
        if previous is None:
            return None, empty

        current_time = datetime.fromisoformat(current_sampled_at.replace("Z", "+00:00"))
        previous_time = datetime.fromisoformat(previous.sampled_at.replace("Z", "+00:00"))
        interval_seconds = max(0.0, (current_time - previous_time).total_seconds())
        if interval_seconds <= 0:
            return None, empty

        def delta_and_rate(current_value: int | None, previous_value: int | None) -> tuple[int | None, float | None]:
            if current_value is None or previous_value is None or current_value < previous_value:
                return None, None
            delta = current_value - previous_value
            return delta, round(delta / interval_seconds, 4)

        io_read_delta, io_read_rate = delta_and_rate(io.read_bytes if io else None, previous.io_read_bytes)
        io_write_delta, io_write_rate = delta_and_rate(io.write_bytes if io else None, previous.io_write_bytes)
        rx_delta, rx_rate = delta_and_rate(net.bytes_recv, previous.network_rx_bytes)
        tx_delta, tx_rate = delta_and_rate(net.bytes_sent, previous.network_tx_bytes)
        return round(interval_seconds, 4), {
            "io_read_delta_bytes": io_read_delta,
            "io_write_delta_bytes": io_write_delta,
            "io_read_bytes_per_sec": io_read_rate,
            "io_write_bytes_per_sec": io_write_rate,
            "network_rx_delta_bytes": rx_delta,
            "network_tx_delta_bytes": tx_delta,
            "network_rx_bytes_per_sec": rx_rate,
            "network_tx_bytes_per_sec": tx_rate,
        }
