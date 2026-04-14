from __future__ import annotations

import asyncio

from backend.engine.task_gate import TaskExecutionGate


def test_task_gate_waits_in_fifo_order():
    gate = TaskExecutionGate()
    events: list[tuple[int, str, int, int]] = []

    async def worker(task_id: int, delay: float) -> None:
        async with gate.acquire(task_id) as grant:
            events.append((task_id, "enter", grant.initial_position, grant.wait_ms))
            await asyncio.sleep(delay)
            events.append((task_id, "exit", grant.initial_position, grant.wait_ms))

    async def main() -> None:
        first = asyncio.create_task(worker(1, 0.05))
        await asyncio.sleep(0.01)
        second = asyncio.create_task(worker(2, 0.0))
        await asyncio.gather(first, second)

    asyncio.run(main())

    assert events[0][0] == 1
    assert events[1][0] == 1
    second_enter = next(item for item in events if item[0] == 2 and item[1] == "enter")
    assert second_enter[2] == 2
    assert second_enter[3] > 0
