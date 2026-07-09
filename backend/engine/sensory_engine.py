from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

import psutil
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.engine.config_store import ConfigStore
from backend.models import Post, SensorySnapshot
from backend.utils.serde import json_dumps
from backend.utils.time import utcnow, utcnow_iso

# Optional host root for host-scope sampling (e.g. docker bind-mount / as /host:ro).
DEFAULT_HOST_ROOT = "/host"


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
        scope = await self._resolve_scope()
        metrics = self._collect_metrics(scope)
        previous = await self._latest_snapshot()
        now_iso = utcnow_iso()
        interval_seconds, deltas = self._compute_deltas(previous, now_iso, metrics["io"], metrics["net"])

        snapshot = SensorySnapshot(
            source=scope,
            sampled_at=now_iso,
            cpu_percent=metrics["cpu_percent"],
            memory_percent=metrics["memory_percent"],
            io_read_bytes=metrics["io"].read_bytes if metrics["io"] else None,
            io_write_bytes=metrics["io"].write_bytes if metrics["io"] else None,
            io_read_delta_bytes=deltas["io_read_delta_bytes"],
            io_write_delta_bytes=deltas["io_write_delta_bytes"],
            io_read_bytes_per_sec=deltas["io_read_bytes_per_sec"],
            io_write_bytes_per_sec=deltas["io_write_bytes_per_sec"],
            disk_usage_percent=metrics["disk_usage_percent"],
            network_rx_bytes=metrics["net"].bytes_recv,
            network_tx_bytes=metrics["net"].bytes_sent,
            network_rx_delta_bytes=deltas["network_rx_delta_bytes"],
            network_tx_delta_bytes=deltas["network_tx_delta_bytes"],
            network_rx_bytes_per_sec=deltas["network_rx_bytes_per_sec"],
            network_tx_bytes_per_sec=deltas["network_tx_bytes_per_sec"],
            sample_interval_seconds=interval_seconds,
            load_average=metrics["load_average"],
            api_latency_ms=None,
            tags="[]",
            translated_text="",
            persona_id=None,
            is_in_blind_zone=0,
        )
        labels = await self._apply_labels(snapshot)
        # Always annotate sampling scope so UI/ops can distinguish container vs host readings.
        scope_tag = f"scope:{scope}"
        if scope_tag not in labels:
            labels.append(scope_tag)
        snapshot.tags = json_dumps(labels)
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

    async def _resolve_scope(self) -> str:
        configured = (await self.config_store.get("sensory.source_mode", "container") or "container").strip().lower()
        if configured in {"host", "host_preferred"}:
            if self._host_root().exists():
                return "host"
            # Fall back transparently when host root is not mounted.
            return "container"
        if configured in {"container", "container_runtime", "cgroup"}:
            return "container"
        return configured or "container"

    def _host_root(self) -> Path:
        return Path(os.getenv("SENSORY_HOST_ROOT", DEFAULT_HOST_ROOT))

    def _collect_metrics(self, scope: str) -> dict:
        if scope == "host":
            host_metrics = self._collect_host_metrics()
            if host_metrics is not None:
                return host_metrics
        return self._collect_container_metrics()

    def _collect_container_metrics(self) -> dict:
        disk = psutil.disk_usage(str(os.getcwd()))
        net = psutil.net_io_counters()
        io = psutil.disk_io_counters()
        try:
            load = os.getloadavg()[0]
        except (AttributeError, OSError):
            load = None
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": disk.percent,
            "load_average": load,
            "io": io,
            "net": net,
        }

    def _collect_host_metrics(self) -> dict | None:
        host_root = self._host_root()
        if not host_root.exists():
            return None

        meminfo = host_root / "proc/meminfo"
        loadavg = host_root / "proc/loadavg"
        # Disk: prefer host root mount when available.
        disk_path = host_root if host_root.is_dir() else Path("/")
        try:
            disk = psutil.disk_usage(str(disk_path))
            disk_percent = disk.percent
        except OSError:
            disk_percent = psutil.disk_usage("/").percent

        memory_percent = None
        if meminfo.exists():
            try:
                values: dict[str, int] = {}
                for line in meminfo.read_text(encoding="utf-8", errors="ignore").splitlines():
                    parts = line.replace(":", " ").split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        values[parts[0]] = int(parts[1])
                total = values.get("MemTotal")
                available = values.get("MemAvailable")
                if total and available is not None and total > 0:
                    memory_percent = round(100.0 * (1.0 - (available / total)), 2)
            except OSError:
                memory_percent = None
        if memory_percent is None:
            memory_percent = psutil.virtual_memory().percent

        load = None
        if loadavg.exists():
            try:
                load = float(loadavg.read_text(encoding="utf-8", errors="ignore").split()[0])
            except (OSError, ValueError, IndexError):
                load = None
        if load is None:
            try:
                load = os.getloadavg()[0]
            except (AttributeError, OSError):
                load = None

        # CPU/network/io still come from the process namespace; labels make the scope explicit.
        net = psutil.net_io_counters()
        io = psutil.disk_io_counters()
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": memory_percent,
            "disk_usage_percent": disk_percent,
            "load_average": load,
            "io": io,
            "net": net,
        }

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
        return 0 <= (utcnow() - published).total_seconds() <= blind_minutes * 60

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
