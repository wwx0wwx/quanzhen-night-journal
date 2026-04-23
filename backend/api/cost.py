from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_cost_monitor
from backend.database import get_session
from backend.engine.cost_monitor import CostMonitor
from backend.models import CostRecord
from backend.security.auth import get_current_user
from backend.utils.response import success

router = APIRouter()


@router.get("/summary")
async def cost_summary(
    period: str = "daily",
    monitor: CostMonitor = Depends(get_cost_monitor),
    _user=Depends(get_current_user),
) -> object:
    return success(await monitor.get_summary(period))


@router.get("/records")
async def cost_records(
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    rows = await db.scalars(select(CostRecord).order_by(desc(CostRecord.created_at)).limit(200))
    items = [
        {
            "id": row.id,
            "task_id": row.task_id,
            "call_type": row.call_type,
            "model_id": row.model_id,
            "token_input": row.token_input,
            "token_output": row.token_output,
            "token_total": row.token_total,
            "cost_estimate": row.cost_estimate,
            "currency": row.currency,
            "created_at": row.created_at,
            "response_latency_ms": row.response_latency_ms,
        }
        for row in rows
    ]
    return success(items)


@router.get("/budget-status")
async def budget_status(
    monitor: CostMonitor = Depends(get_cost_monitor),
    _user=Depends(get_current_user),
) -> object:
    return success((await monitor.check_budget()).model_dump())


@router.post("/wake-up")
async def wake_up(
    monitor: CostMonitor = Depends(get_cost_monitor),
    _user=Depends(get_current_user),
) -> object:
    await monitor.wake_up()
    return success({"woke_up": True})


@router.post("/hibernate")
async def hibernate(
    monitor: CostMonitor = Depends(get_cost_monitor),
    _user=Depends(get_current_user),
) -> object:
    await monitor.hibernate()
    return success({"hibernating": True})
