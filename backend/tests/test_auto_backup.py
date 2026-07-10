from __future__ import annotations

import asyncio

from backend.database import get_sessionmaker
from backend.engine.config_store import ConfigStore
from backend.scheduler.jobs import run_auto_database_backup


def test_auto_database_backup_job_prunes_auto_files(authed_client):
    async def _enable() -> None:
        async with get_sessionmaker()() as db:
            store = ConfigStore(db)
            await store.set("backup.auto_enabled", "1", category="backup")
            await store.set("backup.keep_count", "2", category="backup")
            await db.commit()

    asyncio.run(_enable())

    for _ in range(3):
        asyncio.run(run_auto_database_backup())

    listing = authed_client.get("/api/ghost/database-backups")
    assert listing.status_code == 200
    auto_files = [item for item in listing.json()["data"] if item["automatic"]]
    assert len(auto_files) == 2
    assert all(item["filename"].startswith("auto-") for item in auto_files)

    status = authed_client.get("/api/ghost/backup-status")
    assert status.status_code == 200
    assert status.json()["data"]["last_auto_ok"] is True
    assert len(status.json()["data"]["recent"]) == 2
