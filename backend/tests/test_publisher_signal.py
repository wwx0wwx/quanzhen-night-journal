from __future__ import annotations

import asyncio
import json

from backend.config import get_settings
from backend.publisher.hugo_publisher import HugoPublisher


def test_wait_for_build_requires_matching_signal(tmp_path, monkeypatch):
    signal_path = tmp_path / ".build_signal"
    status_path = tmp_path / "build_status.json"
    # Stale ok from a previous build must not be accepted.
    status_path.write_text(json.dumps({"status": "ok", "signal": "old-signal"}), encoding="utf-8")
    monkeypatch.setenv("BUILD_SIGNAL_FILE", str(signal_path))
    monkeypatch.setenv("BUILD_STATUS_FILE", str(status_path))
    get_settings.cache_clear()

    publisher = HugoPublisher(get_settings())

    async def _run() -> tuple[bool, str]:
        async def _flip() -> None:
            await asyncio.sleep(0.2)
            status_path.write_text(
                json.dumps({"status": "ok", "signal": "new-signal", "built_at": "now"}),
                encoding="utf-8",
            )

        asyncio.create_task(_flip())
        return await publisher._wait_for_build(expected_signal="new-signal", timeout=5)

    ok, detail = asyncio.run(_run())
    assert ok is True
    assert detail == ""
    get_settings.cache_clear()


def test_wait_for_build_times_out_on_stale_ok(tmp_path, monkeypatch):
    status_path = tmp_path / "build_status.json"
    status_path.write_text(json.dumps({"status": "ok", "signal": "stale"}), encoding="utf-8")
    monkeypatch.setenv("BUILD_STATUS_FILE", str(status_path))
    get_settings.cache_clear()
    publisher = HugoPublisher(get_settings())

    ok, detail = asyncio.run(publisher._wait_for_build(expected_signal="expected", timeout=2))
    assert ok is False
    assert detail == "hugo_build_timeout"
    get_settings.cache_clear()
