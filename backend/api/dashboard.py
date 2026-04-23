from __future__ import annotations

from collections import Counter
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import (
    get_config_store,
    get_cost_monitor,
    get_memory_engine,
    get_persona_engine,
)
from backend.api.serializers import post_to_dict, task_to_dict
from backend.database import get_session
from backend.engine.config_store import ConfigStore
from backend.engine.cost_monitor import CostMonitor
from backend.engine.memory_engine import MemoryEngine
from backend.engine.persona_engine import PersonaEngine
from backend.models import GenerationTask, Post, PublicPageView
from backend.security.auth import get_current_user
from backend.utils.response import success

router = APIRouter()


@router.get("")
async def dashboard(
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
    cost_monitor: CostMonitor = Depends(get_cost_monitor),
    persona_engine: PersonaEngine = Depends(get_persona_engine),
    memory_engine: MemoryEngine = Depends(get_memory_engine),
    _user=Depends(get_current_user),
) -> object:
    posts = list(await db.scalars(select(Post).order_by(desc(Post.created_at)).limit(5)))
    tasks = list(await db.scalars(select(GenerationTask).order_by(desc(GenerationTask.started_at)).limit(8)))
    latest_post = posts[0] if posts else None

    persona_score = 80.0
    memory_score = 80.0
    if latest_post and latest_post.persona_id:
        persona_score = await persona_engine.calculate_stability_score(latest_post.persona_id)
        memory_score = await memory_engine.calculate_coherence_score(latest_post.persona_id)

    post_map = {post.id: post for post in posts}
    task_post_ids = [task.post_id for task in tasks if task.post_id and task.post_id not in post_map]
    if task_post_ids:
        extra_posts = await db.scalars(select(Post).where(Post.id.in_(task_post_ids)))
        for row in extra_posts:
            post_map[row.id] = row
    task_map = {task.id: task for task in tasks}
    post_task_ids = [post.task_id for post in posts if post.task_id and post.task_id not in task_map]
    if post_task_ids:
        extra_tasks = await db.scalars(select(GenerationTask).where(GenerationTask.id.in_(post_task_ids)))
        for row in extra_tasks:
            task_map[row.id] = row

    recent_tasks = []
    attention_items = []
    task_counter = Counter()
    for task in tasks:
        task_data = task_to_dict(task, post_map.get(task.post_id))
        recent_tasks.append(task_data)
        task_counter[task.status] += 1

        if task.status in {"failed", "circuit_open"}:
            attention_items.append(
                {
                    "severity": "error",
                    "task_id": task.id,
                    "label": task.error_code or task.status,
                    "message": task.error_message or "任务执行失败",
                }
            )
        elif task.status == "waiting_human_signoff":
            attention_items.append(
                {
                    "severity": "warning",
                    "task_id": task.id,
                    "label": "waiting_human_signoff",
                    "message": "高风险稿件等待人工签发",
                }
            )

        elif task_data["publish_decision_path"] == "human_approved_legacy_inferred":
            attention_items.append(
                {
                    "severity": "warning",
                    "task_id": task.id,
                    "label": "legacy_publish_decision",
                    "message": "已发布高风险稿件的人工签发路径来自历史记录推断，建议复核。",
                }
            )

    llm_ready = bool(await config_store.get("llm.base_url", "")) and bool(await config_store.get("llm.model_id", ""))
    embedding_ready = bool(await config_store.get("embedding.base_url", "")) and bool(
        await config_store.get("embedding.model_id", "")
    )
    system_initialized = (await config_store.get("system.initialized", "0")) == "1"
    domain_enabled = (await config_store.get("site.domain_enabled", "0")) == "1"
    today_prefix = date.today().isoformat()
    today_page_views = (
        await db.scalar(select(func.count(PublicPageView.id)).where(PublicPageView.created_at.like(f"{today_prefix}%")))
        or 0
    )
    domain_status = {
        "domain": await config_store.get("site.domain", "") or "",
        "enabled": domain_enabled,
        "status": await config_store.get("site.domain_status", "disabled") or "disabled",
        "reason": await config_store.get("site.domain_reason", "") or "",
        "checked_at": await config_store.get("site.domain_checked_at", "") or "",
        "base_url": await config_store.get("hugo.base_url", "/") or "/",
    }

    return success(
        {
            "recent_posts": [post_to_dict(item, task_map.get(item.task_id)) for item in posts],
            "recent_tasks": recent_tasks,
            "cost": await cost_monitor.get_summary("daily"),
            "persona_stability": persona_score,
            "memory_coherence": memory_score,
            "risk_overview": {
                "failed": task_counter["failed"],
                "circuit_open": task_counter["circuit_open"],
                "waiting_human_signoff": task_counter["waiting_human_signoff"],
            },
            "attention_items": attention_items[:5],
            "domain_status": domain_status,
            "click_stats": {
                "today_page_views": int(today_page_views),
            },
            "config_status": {
                "system_initialized": system_initialized,
                "llm_ready": llm_ready,
                "embedding_ready": embedding_ready,
                "domain_enabled": domain_enabled,
            },
        }
    )
