from __future__ import annotations

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from backend.config import get_settings
from backend.database import database_file_from_url, get_sessionmaker
from backend.models import SystemConfig
from backend.scheduler.jobs import (
    ensure_seed_persona,
    memory_decay_job,
    memory_reflection_job,
    scheduled_generation_job,
    sensory_sample_job,
)


DEFAULT_SCHEDULES = {
    "schedule.cron_expression": "0 2 * * *",
    "schedule.review_cron": "0 3 * * 0",
    "schedule.decay_cron": "0 4 * * *",
    "schedule.sample_interval_minutes": "5",
}


async def _load_schedule_settings() -> dict[str, str]:
    session_factory = get_sessionmaker()
    async with session_factory() as db:
        rows = await db.scalars(
            select(SystemConfig).where(SystemConfig.key.in_(tuple(DEFAULT_SCHEDULES.keys())))
        )
        values = {row.key: row.value for row in rows}
    return {key: str(values.get(key) or default) for key, default in DEFAULT_SCHEDULES.items()}


def _sample_trigger(minutes_text: str) -> CronTrigger:
    try:
        minutes = int(minutes_text)
    except (TypeError, ValueError):
        minutes = 5
    minutes = max(1, min(minutes, 59))
    return CronTrigger.from_crontab(f"*/{minutes} * * * *")


async def reload_scheduler(scheduler: AsyncIOScheduler) -> AsyncIOScheduler:
    values = await _load_schedule_settings()
    scheduler.add_job(
        scheduled_generation_job,
        trigger=CronTrigger.from_crontab(values["schedule.cron_expression"]),
        id="scheduled_generation",
        replace_existing=True,
    )
    scheduler.add_job(
        sensory_sample_job,
        trigger=_sample_trigger(values["schedule.sample_interval_minutes"]),
        id="sensory_sample",
        replace_existing=True,
    )
    scheduler.add_job(
        memory_decay_job,
        trigger=CronTrigger.from_crontab(values["schedule.decay_cron"]),
        id="memory_decay",
        replace_existing=True,
    )
    scheduler.add_job(
        memory_reflection_job,
        trigger=CronTrigger.from_crontab(values["schedule.review_cron"]),
        id="memory_reflection",
        replace_existing=True,
    )
    return scheduler


async def setup_scheduler() -> AsyncIOScheduler:
    settings = get_settings()
    db_file = database_file_from_url(settings.database_url)
    scheduler = AsyncIOScheduler(
        timezone="UTC",
        jobstores={
            "default": SQLAlchemyJobStore(url=f"sqlite:///{db_file.as_posix()}" if db_file else "sqlite:///data/jobs.db")
        },
    )
    await ensure_seed_persona()
    await reload_scheduler(scheduler)
    scheduler.start()
    return scheduler
