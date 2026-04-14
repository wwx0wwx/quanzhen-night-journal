from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from backend.config import get_settings
from backend.database import close_database


@pytest.fixture()
def client(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    content_dir = tmp_path / "content"
    draft_dir = tmp_path / "draft_review"
    automation_dir = tmp_path / "automation"
    public_dir = tmp_path / "public"
    data_dir.mkdir()
    content_dir.mkdir()
    (content_dir / "posts").mkdir()
    draft_dir.mkdir()
    automation_dir.mkdir()
    public_dir.mkdir()
    (data_dir / "build_status.json").write_text(json.dumps({"status": "ok"}), encoding="utf-8")

    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{(data_dir / 'test.db').as_posix()}")
    monkeypatch.setenv("HUGO_CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("HUGO_PUBLIC_DIR", str(public_dir))
    monkeypatch.setenv("BUILD_SIGNAL_FILE", str(data_dir / ".build_signal"))
    monkeypatch.setenv("BUILD_STATUS_FILE", str(data_dir / "build_status.json"))
    monkeypatch.setenv("SEED_CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("SEED_DRAFT_DIR", str(draft_dir))
    monkeypatch.setenv("AUTOMATION_DIR", str(automation_dir))
    monkeypatch.setenv("JWT_SECRET", "test-secret-with-safe-length-1234567890")
    monkeypatch.setenv("ALLOW_FAKE_LLM", "true")

    get_settings.cache_clear()

    from backend.main import app

    with TestClient(app) as test_client:
        yield test_client

    get_settings.cache_clear()
    import asyncio

    asyncio.run(close_database())


@pytest.fixture()
def authed_client(client):
    client.post(
        "/api/setup/complete",
        json={
            "new_password": "quanzhen123",
            "site_title": "全真夜记",
            "site_subtitle": "",
            "site_domain": "",
            "llm_base_url": "",
            "llm_api_key": "",
            "llm_model_id": "",
            "embedding_base_url": "",
            "embedding_api_key": "",
            "embedding_model_id": "",
        },
    )
    client.post("/api/auth/login", json={"username": "admin", "password": "quanzhen123"})
    return client
