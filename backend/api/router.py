from __future__ import annotations

from fastapi import APIRouter

from backend.api import (
    audit,
    auth,
    config,
    cost,
    dashboard,
    events,
    folder_monitors,
    ghost,
    health,
    memories,
    personas,
    posts,
    sensory,
    setup,
    tasks,
    webhook,
)


router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(config.router, prefix="/config", tags=["config"])
router.include_router(setup.router, prefix="/setup", tags=["setup"])
router.include_router(personas.router, prefix="/personas", tags=["personas"])
router.include_router(memories.router, prefix="/memories", tags=["memories"])
router.include_router(posts.router, prefix="/posts", tags=["posts"])
router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
router.include_router(sensory.router, prefix="/sensory", tags=["sensory"])
router.include_router(events.router, prefix="/events", tags=["events"])
router.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
router.include_router(cost.router, prefix="/cost", tags=["cost"])
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(ghost.router, prefix="/ghost", tags=["ghost"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
router.include_router(folder_monitors.router, prefix="/folder-monitors", tags=["folder-monitors"])
router.include_router(audit.router, prefix="/audit", tags=["audit"])
