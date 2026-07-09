from __future__ import annotations

import threading
import time
from collections import Counter
from typing import Any


class ProcessMetrics:
    """Lightweight in-process counters for operational observability."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started_at = time.time()
        self._counters: Counter[str] = Counter()
        self._gauges: dict[str, float] = {}
        self._last_events: dict[str, str] = {}

    def incr(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[name] += amount

    def set_gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._gauges[name] = float(value)

    def note_event(self, name: str, detail: str) -> None:
        with self._lock:
            self._last_events[name] = detail[:500]

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "uptime_seconds": round(time.time() - self._started_at, 2),
                "started_at_unix": self._started_at,
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "last_events": dict(self._last_events),
            }


METRICS = ProcessMetrics()
