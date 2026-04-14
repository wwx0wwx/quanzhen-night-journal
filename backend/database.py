from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import aiosqlite
import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from backend.config import Settings, get_settings


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False},
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _sessionmaker


async def get_session() -> AsyncIterator[AsyncSession]:
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        yield session


async def init_database(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.hugo_post_path.mkdir(parents=True, exist_ok=True)
    settings.hugo_public_path.mkdir(parents=True, exist_ok=True)
    settings.ghost_path.mkdir(parents=True, exist_ok=True)
    settings.build_signal_path.parent.mkdir(parents=True, exist_ok=True)
    settings.build_status_path.parent.mkdir(parents=True, exist_ok=True)

    password_hash = bcrypt.hashpw(b"quanzhen", bcrypt.gensalt()).decode("utf-8")
    schema_sql = settings.schema_path.read_text(encoding="utf-8").replace(
        "$PLACEHOLDER_HASH$",
        password_hash,
    )

    async with aiosqlite.connect(settings.database_path) as conn:
        await conn.execute("PRAGMA encoding = 'UTF-8'")
        await conn.executescript(schema_sql)
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_vectors (
                memory_id INTEGER PRIMARY KEY,
                embedding TEXT NOT NULL DEFAULT '[]'
            );
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS post_vectors (
                post_id INTEGER PRIMARY KEY,
                embedding TEXT NOT NULL DEFAULT '[]'
            );
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_event_definitions (
                action TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                target_label TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        await _ensure_column(conn, "generation_tasks", "queue_wait_ms", "INTEGER NOT NULL DEFAULT 0")
        await _ensure_column(conn, "generation_tasks", "trace_json", "TEXT NOT NULL DEFAULT '[]'")
        await _ensure_column(conn, "generation_tasks", "error_code", "TEXT")
        await conn.commit()


async def close_database() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None


def database_file_from_url(url: str) -> Path | None:
    prefix = "sqlite+aiosqlite:///"
    if url.startswith(prefix):
        return Path(url[len(prefix) :])
    return None


async def _ensure_column(conn: aiosqlite.Connection, table: str, column: str, ddl: str) -> None:
    existing = set()
    async with conn.execute(f"PRAGMA table_info({table})") as cursor:
        async for row in cursor:
            existing.add(row[1])
    if column in existing:
        return
    await conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
