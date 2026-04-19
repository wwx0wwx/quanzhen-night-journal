from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from backend.database import get_sessionmaker
from backend.models import CostRecord


def test_cost_summary_respects_daily_weekly_and_monthly_windows(monkeypatch, authed_client):
    monkeypatch.setattr(
        "backend.engine.cost_monitor.utcnow",
        lambda: datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc),
    )

    async def seed() -> None:
        session_factory = get_sessionmaker()
        async with session_factory() as db:
            db.add_all(
                [
                    CostRecord(
                        task_id=None,
                        call_type="generation",
                        model_id="gpt-4o-mini",
                        token_input=10,
                        token_output=10,
                        token_total=20,
                        cost_estimate=1.0,
                        currency="USD",
                        created_at="2026-04-19T10:00:00+00:00",
                        response_latency_ms=10,
                    ),
                    CostRecord(
                        task_id=None,
                        call_type="generation",
                        model_id="gpt-4o-mini",
                        token_input=10,
                        token_output=10,
                        token_total=20,
                        cost_estimate=2.0,
                        currency="USD",
                        created_at="2026-04-15T10:00:00+00:00",
                        response_latency_ms=10,
                    ),
                    CostRecord(
                        task_id=None,
                        call_type="generation",
                        model_id="gpt-4o-mini",
                        token_input=10,
                        token_output=10,
                        token_total=20,
                        cost_estimate=4.0,
                        currency="USD",
                        created_at="2026-03-31T10:00:00+00:00",
                        response_latency_ms=10,
                    ),
                ]
            )
            await db.commit()

    asyncio.run(seed())

    daily = authed_client.get("/api/cost/summary", params={"period": "daily"})
    weekly = authed_client.get("/api/cost/summary", params={"period": "weekly"})
    monthly = authed_client.get("/api/cost/summary", params={"period": "monthly"})

    assert daily.status_code == 200
    assert weekly.status_code == 200
    assert monthly.status_code == 200
    assert daily.json()["data"]["cost"] == 1.0
    assert weekly.json()["data"]["cost"] == 3.0
    assert monthly.json()["data"]["cost"] == 3.0
