from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.engine.config_store import ConfigStore
from backend.models import CostRecord
from backend.schemas.cost import BudgetStatus
from backend.utils.time import utcnow_iso


PRICING = {
    "default": (0.50, 1.50),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4.1-mini": (0.40, 1.60),
}


class CostMonitor:
    def __init__(self, db: AsyncSession, config_store: ConfigStore):
        self.db = db
        self.config_store = config_store

    async def record(
        self,
        task_id: int | None,
        call_type: str,
        model_id: str,
        token_in: int,
        token_out: int,
        latency_ms: int = 0,
    ) -> CostRecord:
        estimate = await self.estimate_cost(token_in, token_out, model_id)
        record = CostRecord(
            task_id=task_id,
            call_type=call_type,
            model_id=model_id,
            token_input=token_in,
            token_output=token_out,
            token_total=token_in + token_out,
            cost_estimate=estimate,
            currency="USD",
            created_at=utcnow_iso(),
            response_latency_ms=latency_ms,
        )
        self.db.add(record)
        await self.db.flush()
        await self.check_budget()
        return record

    async def check_budget(self) -> BudgetStatus:
        limit = float(await self.config_store.get("budget.daily_limit_usd", "99999") or 99999.0)
        today_prefix = date.today().isoformat()
        spent = await self.db.scalar(
            select(func.coalesce(func.sum(CostRecord.cost_estimate), 0.0)).where(
                CostRecord.created_at.like(f"{today_prefix}%")
            )
        ) or 0.0
        is_hibernating = spent >= limit
        await self.config_store.set("budget.is_hibernating", "1" if is_hibernating else "0", category="budget")
        remaining = max(0.0, limit - float(spent))
        return BudgetStatus(remaining=round(remaining, 4), limit=limit, is_hibernating=is_hibernating)

    async def wake_up(self) -> None:
        await self.config_store.set("budget.is_hibernating", "0", category="budget")

    async def estimate_cost(self, token_in: int, token_out: int, model_id: str) -> float:
        input_price, output_price = PRICING.get(model_id, PRICING["default"])
        total = (token_in / 1_000_000) * input_price + (token_out / 1_000_000) * output_price
        return round(total, 6)

    async def get_summary(self, period: str) -> dict:
        if period == "weekly":
            pattern = date.today().strftime("%Y-%m")
        elif period == "monthly":
            pattern = date.today().strftime("%Y-%m")
        else:
            pattern = date.today().isoformat()
        total_cost = await self.db.scalar(
            select(func.coalesce(func.sum(CostRecord.cost_estimate), 0.0)).where(
                CostRecord.created_at.like(f"{pattern}%")
            )
        ) or 0.0
        total_tokens = await self.db.scalar(
            select(func.coalesce(func.sum(CostRecord.token_total), 0)).where(
                CostRecord.created_at.like(f"{pattern}%")
            )
        ) or 0
        return {"period": period, "cost": round(float(total_cost), 6), "tokens": int(total_tokens)}
