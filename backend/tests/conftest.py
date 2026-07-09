from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.config import get_settings
from backend.database import close_database


def _start_build_status_mirror(signal_path: Path, status_path: Path) -> tuple[threading.Event, threading.Thread]:
    """Simulate hugo-builder: whenever signal changes, write matching status=ok."""
    stop = threading.Event()
    last = {"value": None}

    def _loop() -> None:
        while not stop.is_set():
            try:
                if signal_path.exists():
                    signal = signal_path.read_text(encoding="utf-8").strip()
                    if signal and signal != last["value"]:
                        status_path.write_text(
                            json.dumps(
                                {
                                    "status": "ok",
                                    "signal": signal,
                                    "built_at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
                                }
                            ),
                            encoding="utf-8",
                        )
                        last["value"] = signal
            except OSError:
                pass
            stop.wait(0.05)

    thread = threading.Thread(target=_loop, name="test-hugo-build-mirror", daemon=True)
    thread.start()
    return stop, thread


@pytest.fixture()
def client(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    content_dir = tmp_path / "content"
    draft_dir = tmp_path / "draft_review"
    automation_dir = tmp_path / "automation"
    public_dir = tmp_path / "public"
    presets_dir = tmp_path / "presets"
    data_dir.mkdir()
    content_dir.mkdir()
    (content_dir / "posts").mkdir()
    draft_dir.mkdir()
    automation_dir.mkdir()
    public_dir.mkdir()
    presets_dir.mkdir()
    signal_path = data_dir / ".build_signal"
    status_path = data_dir / "build_status.json"
    status_path.write_text(json.dumps({"status": "ok", "signal": ""}), encoding="utf-8")
    stop_mirror, mirror_thread = _start_build_status_mirror(signal_path, status_path)

    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{(data_dir / 'test.db').as_posix()}")
    monkeypatch.setenv("HUGO_CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("HUGO_PUBLIC_DIR", str(public_dir))
    monkeypatch.setenv("BUILD_SIGNAL_FILE", str(signal_path))
    monkeypatch.setenv("BUILD_STATUS_FILE", str(status_path))
    monkeypatch.setenv("SEED_CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("SEED_DRAFT_DIR", str(draft_dir))
    monkeypatch.setenv("AUTOMATION_DIR", str(automation_dir))
    monkeypatch.setenv("PRESETS_DIR", str(presets_dir))
    monkeypatch.setenv("DEFAULT_PRESET", "quanzhen")

    real_preset = Path(__file__).resolve().parent.parent.parent / "presets" / "quanzhen"
    test_preset = presets_dir / "quanzhen"
    test_preset.mkdir()
    for name in ("persona.json", "memories.json"):
        src = real_preset / name
        if src.exists():
            (test_preset / name).write_bytes(src.read_bytes())
    monkeypatch.setenv("JWT_SECRET", "test-secret-with-safe-length-1234567890")
    monkeypatch.setenv("ALLOW_FAKE_LLM", "true")

    get_settings.cache_clear()

    from backend.main import app

    with TestClient(app) as test_client:
        yield test_client

    stop_mirror.set()
    mirror_thread.join(timeout=1)
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
