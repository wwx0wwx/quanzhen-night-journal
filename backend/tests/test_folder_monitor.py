from __future__ import annotations

import asyncio
from types import SimpleNamespace

from watchdog.observers.polling import PollingObserver

from backend.engine.folder_monitor_manager import FolderMonitorManager, _FolderHandler


class _DummyManager:
    def __init__(self):
        self.loop = object()

    async def process_file(self, monitor_path: str, file_path: str) -> None:
        return None


def _event(path: str, is_directory: bool = False):
    return SimpleNamespace(src_path=path, is_directory=is_directory)


def test_folder_monitor_manager_uses_polling_observer():
    loop = asyncio.new_event_loop()
    try:
        manager = FolderMonitorManager(loop)
        assert isinstance(manager._observer, PollingObserver)
    finally:
        loop.close()


def test_folder_handler_debounces_duplicate_events(monkeypatch):
    manager = _DummyManager()
    handler = _FolderHandler(manager, "/watch", ["md"])
    calls: list[tuple[str, str]] = []

    def fake_submit(coro, loop):
        try:
            coro.close()
        except RuntimeError:
            pass
        calls.append(("/watch", "note.md"))
        return None

    times = iter([10.0, 10.2, 12.0])
    monkeypatch.setattr("backend.engine.folder_monitor_manager.time.monotonic", lambda: next(times))
    monkeypatch.setattr("backend.engine.folder_monitor_manager.asyncio.run_coroutine_threadsafe", fake_submit)

    handler.on_created(_event("note.md"))
    handler.on_modified(_event("note.md"))
    handler.on_modified(_event("note.md"))

    assert len(calls) == 2


def test_folder_handler_ignores_unlisted_suffix(monkeypatch):
    manager = _DummyManager()
    handler = _FolderHandler(manager, "/watch", ["md"])
    called = False

    def fake_submit(coro, loop):
        nonlocal called
        called = True
        try:
            coro.close()
        except RuntimeError:
            pass
        return None

    monkeypatch.setattr("backend.engine.folder_monitor_manager.asyncio.run_coroutine_threadsafe", fake_submit)

    handler.on_created(_event("image.png"))

    assert called is False
