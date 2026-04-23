from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass


@dataclass(slots=True)
class QueueGrant:
    initial_position: int
    wait_ms: int


class TaskExecutionGate:
    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._condition: asyncio.Condition | None = None
        self._queue: deque[int] = deque()
        self._active_task_id: int | None = None

    def _ensure_state(self) -> asyncio.Condition:
        loop = asyncio.get_running_loop()
        if self._loop is not loop or self._condition is None:
            self._loop = loop
            self._condition = asyncio.Condition()
            self._queue = deque()
            self._active_task_id = None
        return self._condition

    @asynccontextmanager
    async def acquire(self, task_id: int) -> AsyncIterator[QueueGrant]:
        condition = self._ensure_state()
        enqueued_at = time.monotonic()
        initial_position = 0
        acquired = False

        async with condition:
            self._queue.append(task_id)
            initial_position = len(self._queue) + (1 if self._active_task_id is not None else 0)
            condition.notify_all()
            try:
                while self._active_task_id is not None or self._queue[0] != task_id:
                    await condition.wait()
                self._queue.popleft()
                self._active_task_id = task_id
                acquired = True
            except BaseException:
                if task_id in self._queue:
                    self._queue.remove(task_id)
                    condition.notify_all()
                raise

        wait_ms = int((time.monotonic() - enqueued_at) * 1000)
        try:
            yield QueueGrant(initial_position=initial_position, wait_ms=wait_ms)
        finally:
            if acquired:
                async with condition:
                    if self._active_task_id == task_id:
                        self._active_task_id = None
                        condition.notify_all()


TASK_GATE = TaskExecutionGate()
