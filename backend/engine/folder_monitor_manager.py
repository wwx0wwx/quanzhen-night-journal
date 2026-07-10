from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from sqlalchemy import select
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

from backend.database import get_sessionmaker
from backend.engine.runtime_factory import build_generation_runtime
from backend.models import FolderMonitor
from backend.security.encryption import ConfigEncryptor, ensure_encryptor


class _FolderHandler(FileSystemEventHandler):
    def __init__(self, manager: FolderMonitorManager, monitor_path: str, file_types: list[str]):
        self.manager = manager
        self.monitor_path = monitor_path
        self.file_types = {item.lower().lstrip(".") for item in file_types}
        self.debounce_window = 1.5
        self._last_seen: dict[str, float] = {}

    def on_created(self, event: FileSystemEvent) -> None:
        self._handle(event)

    def on_modified(self, event: FileSystemEvent) -> None:
        self._handle(event)

    def _handle(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        normalized_path = str(Path(event.src_path))
        suffix = Path(normalized_path).suffix.lower().lstrip(".")
        if self.file_types and suffix not in self.file_types:
            return
        now = time.monotonic()
        if len(self._last_seen) > 1024:
            self._last_seen = {
                path: seen_at for path, seen_at in self._last_seen.items() if now - seen_at < self.debounce_window
            }
        last_seen = self._last_seen.get(normalized_path)
        if last_seen is not None and now - last_seen < self.debounce_window:
            return
        self._last_seen[normalized_path] = now
        asyncio.run_coroutine_threadsafe(
            self.manager.process_file(self.monitor_path, normalized_path),
            self.manager.loop,
        )


class FolderMonitorManager:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        # Polling is slower than inotify, but it is much more reliable on Docker-mounted paths.
        self._observer = PollingObserver(timeout=1.0)
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        await self.reload()
        self._observer.start()
        self._started = True

    async def reload(self) -> None:
        was_started = self._started
        if self._observer.is_alive():
            self._observer.stop()
            self._observer.join(timeout=2)
        self._observer = PollingObserver(timeout=1.0)
        self._started = False
        session_factory = get_sessionmaker()
        async with session_factory() as db:
            rows = await db.scalars(select(FolderMonitor).where(FolderMonitor.is_active == 1))
            for monitor in rows:
                path = Path(monitor.path)
                if not path.exists() or not path.is_dir():
                    continue
                file_types = ["txt", "md"] if not monitor.file_types else json.loads(monitor.file_types)
                handler = _FolderHandler(self, monitor.path, file_types)
                self._observer.schedule(handler, monitor.path, recursive=False)
        if was_started:
            self._observer.start()
            self._started = True

    def stop(self) -> None:
        if self._observer.is_alive():
            self._observer.stop()
            self._observer.join(timeout=2)
        self._started = False

    async def process_file(self, monitor_path: str, file_path: str) -> None:
        session_factory = get_sessionmaker()
        async with session_factory() as db:
            encryptor = await self._get_encryptor(db)
            (
                _config_store,
                _persona_engine,
                _memory_engine,
                _qa_engine,
                _cost_monitor,
                _sensory_engine,
                event_engine,
                orchestrator,
            ) = build_generation_runtime(db, encryptor)
            payload = {"monitor_path": monitor_path, "file_path": file_path}
            event = await event_engine.create_event(
                "folder_monitor",
                monitor_path,
                payload,
                semantic_hint=f"目录监控捕获文件变更：{Path(file_path).name}",
            )
            persona = await persona_engine.get_active_persona()
            await orchestrator.execute(event, persona=persona)

    async def _get_encryptor(self, db) -> ConfigEncryptor:
        encryptor, created = await ensure_encryptor(db)
        if created:
            await db.commit()
        return encryptor
