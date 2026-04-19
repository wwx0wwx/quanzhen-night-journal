from __future__ import annotations

import asyncio
from urllib.parse import unquote
from pathlib import Path

from sqlalchemy import func, select, text

from backend.api.deps import get_encryptor
from backend.api.ghost import _read_upload_payload
from backend.config import get_settings
from backend.database import get_sessionmaker
from backend.engine.config_store import ConfigStore
from backend.engine.ghost_manager import GhostManager
from backend.models import Memory, MemoryVector, Post, PostVector


def test_ghost_import_restores_vectors(authed_client):
    memory = authed_client.post(
        "/api/memories",
        json={
            "persona_id": 1,
            "level": "L0",
            "content": "主机壳体有一点暖，像夜里没说完的话还贴在手心。",
            "summary": "主机壳体仍有余温。",
            "tags": ["ghost"],
            "source": "hand_written",
            "weight": 1.0,
            "review_status": "reviewed",
            "decay_strategy": "standard",
            "is_core": True,
        },
    )
    assert memory.status_code == 200

    generated = authed_client.post(
        "/api/tasks/trigger",
        json={"trigger_source": "manual", "semantic_hint": "请写一段关于主机余温的夜记", "payload": {"kind": "manual"}},
    )
    assert generated.status_code == 200

    exported = authed_client.post("/api/ghost/export", json={"include_api_keys": False})
    assert exported.status_code == 200
    export_info = exported.json()["data"]

    async def exercise_import() -> None:
        session_factory = get_sessionmaker()
        async with session_factory() as db:
            encryptor = await get_encryptor(db)
            config_store = ConfigStore(db, encryptor)
            manager = GhostManager(db, config_store, get_settings().ghost_path)

            memory_vector_count = await db.scalar(select(func.count()).select_from(MemoryVector))
            post_vector_count = await db.scalar(select(func.count()).select_from(PostVector))
            original_memory_vectors = int(memory_vector_count or 0)
            original_post_vectors = int(post_vector_count or 0)

            await db.execute(text("DELETE FROM post_vectors"))
            await db.execute(text("DELETE FROM memory_vectors"))
            await db.execute(text("DELETE FROM posts"))
            await db.execute(text("DELETE FROM memories"))
            await db.commit()

            payload = Path(export_info["path"]).read_bytes()
            preview = await manager.import_ghost(export_info["filename"], payload, confirm=True)
            await db.commit()

            restored_memories = await db.scalar(select(func.count()).select_from(Memory))
            restored_posts = await db.scalar(select(func.count()).select_from(Post))
            restored_memory_vectors = await db.scalar(select(func.count()).select_from(MemoryVector))
            restored_post_vectors = await db.scalar(select(func.count()).select_from(PostVector))

            assert preview["manifest"]["counts"]["memories"] >= 1
            assert preview["manifest"]["counts"]["posts"] >= 1
            assert int(restored_memories or 0) >= 1
            assert int(restored_posts or 0) >= 1
            assert int(restored_memory_vectors or 0) == original_memory_vectors
            assert int(restored_post_vectors or 0) == original_post_vectors

    asyncio.run(exercise_import())


def test_ghost_export_can_be_downloaded(authed_client):
    exported = authed_client.post("/api/ghost/export", json={"include_api_keys": False})
    assert exported.status_code == 200
    filename = exported.json()["data"]["filename"]

    download = authed_client.get(f"/api/ghost/download/{filename}")
    assert download.status_code == 200
    assert filename in unquote(download.headers.get("content-disposition", ""))
    assert download.content


def test_database_backup_can_be_created_and_downloaded(authed_client):
    backup = authed_client.post("/api/ghost/backup-database")
    assert backup.status_code == 200
    filename = backup.json()["data"]["filename"]

    listing = authed_client.get("/api/ghost/database-backups")
    assert listing.status_code == 200
    assert any(item["filename"] == filename for item in listing.json()["data"])

    download = authed_client.get(f"/api/ghost/download-database-backup/{filename}")
    assert download.status_code == 200
    assert filename in unquote(download.headers.get("content-disposition", ""))
    assert download.content


def test_ghost_upload_rejects_oversized_files(monkeypatch, authed_client):
    monkeypatch.setattr("backend.api.ghost.MAX_GHOST_UPLOAD_BYTES", 128)

    response = authed_client.post(
        "/api/ghost/preview",
        files={"file": ("too-large.ghost", b"x" * 256, "application/octet-stream")},
    )

    assert response.status_code == 413
    assert "上传文件过大" in response.json()["message"]


def test_ghost_upload_reader_stops_once_size_limit_is_exceeded(monkeypatch):
    class FakeUpload:
        def __init__(self) -> None:
            self.calls = 0

        async def read(self, _size: int = -1) -> bytes:
            self.calls += 1
            if self.calls == 1:
                return b"a" * 80
            if self.calls == 2:
                return b"b" * 80
            return b"c" * 80

    monkeypatch.setattr("backend.api.ghost.MAX_GHOST_UPLOAD_BYTES", 100)
    monkeypatch.setattr("backend.api.ghost.UPLOAD_READ_CHUNK_BYTES", 80)

    async def exercise() -> None:
        upload = FakeUpload()
        payload, error_response = await _read_upload_payload(upload)

        assert payload is None
        assert error_response is not None
        assert upload.calls == 2

    asyncio.run(exercise())
