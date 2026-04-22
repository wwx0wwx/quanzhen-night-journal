from __future__ import annotations

import hashlib
import random
from datetime import date, datetime, time as time_value, timedelta, timezone

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from sqlalchemy import select

from backend.config import get_settings
from backend.database import database_file_from_url, get_sessionmaker
from backend.engine.config_store import ConfigStore
from backend.models import SystemConfig
from backend.scheduler.jobs import (
    audit_cleanup_job,
    ensure_seed_persona,
    memory_decay_job,
    memory_reflection_job,
    scheduled_generation_job,
    sensory_sample_job,
)


DEFAULT_SCHEDULES = {
    "schedule.days_per_cycle": "1",
    "schedule.posts_per_cycle": "1",
    "schedule.publish_time": "21:02",
    "schedule.cycle_anchor_date": "",
    "schedule.review_cron": "0 3 * * 0",
    "schedule.decay_cron": "0 4 * * *",
    "schedule.sample_interval_minutes": "5",
}
_scheduler_ref: AsyncIOScheduler | None = None


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


def _publish_trigger(clock_text: str) -> CronTrigger:
    hour, minute = _parse_publish_time(clock_text)
    return CronTrigger(hour=hour, minute=minute)


def _parse_publish_time(clock_text: str) -> tuple[int, int]:
    text = str(clock_text or "").strip()
    try:
        hour_text, minute_text = text.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
    except (AttributeError, ValueError):
        return 21, 2
    if hour not in range(24) or minute not in range(60):
        return 21, 2
    return hour, minute


def _clamp_cycle_count(value: str, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(str(value or "").strip())
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(parsed, maximum))


def _scheduler_timezone():
    scheduler = _scheduler_ref
    return scheduler.timezone if scheduler is not None else timezone.utc


async def _should_publish_today(values: dict[str, str]) -> bool:
    posts_per_cycle = _clamp_cycle_count(values.get("schedule.posts_per_cycle", "1"), default=1, minimum=0, maximum=24)
    if posts_per_cycle <= 0:
        return False

    days_per_cycle = _clamp_cycle_count(values.get("schedule.days_per_cycle", "1"), default=1, minimum=1, maximum=365)
    today = datetime.now(_scheduler_timezone()).date()
    anchor_text = str(values.get("schedule.cycle_anchor_date", "") or "").strip()

    try:
        anchor_date = date.fromisoformat(anchor_text) if anchor_text else None
    except ValueError:
        anchor_date = None

    if anchor_date is None:
        session_factory = get_sessionmaker()
        async with session_factory() as db:
            await ConfigStore(db).set("schedule.cycle_anchor_date", today.isoformat(), category="schedule")
            await db.commit()
        anchor_date = today

    delta_days = (today - anchor_date).days
    if delta_days < 0:
        return False
    return delta_days % days_per_cycle == 0


def _build_followup_run_times(values: dict[str, str], extra_count: int) -> list[datetime]:
    if extra_count <= 0:
        return []

    tz = _scheduler_timezone()
    now_local = datetime.now(tz)
    today = now_local.date()
    hour, minute = _parse_publish_time(values.get("schedule.publish_time", "21:02"))
    start_minute = (hour * 60 + minute) + 90
    end_minute = 23 * 60 + 40

    if start_minute > end_minute:
        start_minute = min((hour * 60 + minute) + 10, 23 * 60 + 55)
        end_minute = 23 * 60 + 59

    seed_source = "|".join(
        [
            today.isoformat(),
            str(values.get("schedule.days_per_cycle", "1")),
            str(values.get("schedule.posts_per_cycle", "1")),
            str(values.get("schedule.publish_time", "21:02")),
        ]
    )
    seed = int(hashlib.sha256(seed_source.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)
    available_minutes = list(range(start_minute, end_minute + 1))
    if not available_minutes:
        return []

    if extra_count >= len(available_minutes):
        selected_minutes = available_minutes
    else:
        selected_minutes = sorted(rng.sample(available_minutes, extra_count))

    run_times = []
    for minute_value in selected_minutes:
        run_at = datetime.combine(
            today,
            time_value(hour=minute_value // 60, minute=minute_value % 60),
            tzinfo=tz,
        )
        if run_at > now_local + timedelta(minutes=1):
            run_times.append(run_at)
    return run_times


def _clear_pending_followups(scheduler: AsyncIOScheduler, *, prefix: str = "scheduled_generation_extra_") -> None:
    for job in scheduler.get_jobs():
        if job.id.startswith(prefix):
            scheduler.remove_job(job.id)


async def scheduled_generation_dispatch_job() -> None:
    values = await _load_schedule_settings()
    if not await _should_publish_today(values):
        return

    await scheduled_generation_job(slot_index=0, scheduled_for=values.get("schedule.publish_time", "21:02"))

    scheduler = _scheduler_ref
    if scheduler is None:
        return

    posts_per_cycle = _clamp_cycle_count(values.get("schedule.posts_per_cycle", "1"), default=1, minimum=0, maximum=24)
    extra_run_times = _build_followup_run_times(values, max(0, posts_per_cycle - 1))
    today_tag = datetime.now(timezone.utc).strftime("%Y%m%d")
    _clear_pending_followups(scheduler, prefix=f"scheduled_generation_extra_{today_tag}_")

    for index, run_at in enumerate(extra_run_times, start=1):
        scheduler.add_job(
            scheduled_generation_job,
            trigger=DateTrigger(run_date=run_at),
            kwargs={
                "slot_index": index,
                "scheduled_for": run_at.astimezone(timezone.utc).isoformat(),
            },
            id=f"scheduled_generation_extra_{today_tag}_{index}",
            replace_existing=True,
        )


async def reload_scheduler(scheduler: AsyncIOScheduler) -> AsyncIOScheduler:
    global _scheduler_ref
    _scheduler_ref = scheduler
    values = await _load_schedule_settings()
    scheduler.add_job(
        scheduled_generation_dispatch_job,
        trigger=_publish_trigger(values["schedule.publish_time"]),
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
    scheduler.add_job(
        audit_cleanup_job,
        trigger=CronTrigger(hour=5, minute=15),
        id="audit_cleanup",
        replace_existing=True,
    )
    return scheduler


async def setup_scheduler() -> AsyncIOScheduler:
    global _scheduler_ref
    settings = get_settings()
    db_file = database_file_from_url(settings.database_url)
    scheduler = AsyncIOScheduler(
        timezone="UTC",
        jobstores={
            "default": SQLAlchemyJobStore(url=f"sqlite:///{db_file.as_posix()}" if db_file else "sqlite:///data/jobs.db")
        },
    )
    _scheduler_ref = scheduler
    await ensure_seed_persona()
    await reload_scheduler(scheduler)
    scheduler.start()
    return scheduler
