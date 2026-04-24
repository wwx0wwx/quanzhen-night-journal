from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path

import aiosqlite
import bcrypt
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

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

        @event.listens_for(_engine.sync_engine, "connect")
        def _set_sqlite_pragmas(dbapi_conn, _connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

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
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS public_page_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL DEFAULT '/',
                page_title TEXT NOT NULL DEFAULT '',
                referrer TEXT NOT NULL DEFAULT '',
                ip_address TEXT NOT NULL DEFAULT '',
                user_agent TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_public_page_views_created
            ON public_page_views (created_at);
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_public_page_views_path_created
            ON public_page_views (path, created_at);
            """
        )
        await _ensure_column(conn, "generation_tasks", "queue_wait_ms", "INTEGER NOT NULL DEFAULT 0")
        await _ensure_column(conn, "generation_tasks", "trace_json", "TEXT NOT NULL DEFAULT '[]'")
        await _ensure_column(conn, "generation_tasks", "error_code", "TEXT")
        await _ensure_column(conn, "sensory_snapshots", "io_read_delta_bytes", "INTEGER")
        await _ensure_column(conn, "sensory_snapshots", "io_write_delta_bytes", "INTEGER")
        await _ensure_column(conn, "sensory_snapshots", "io_read_bytes_per_sec", "REAL")
        await _ensure_column(conn, "sensory_snapshots", "io_write_bytes_per_sec", "REAL")
        await _ensure_column(conn, "sensory_snapshots", "network_rx_delta_bytes", "INTEGER")
        await _ensure_column(conn, "sensory_snapshots", "network_tx_delta_bytes", "INTEGER")
        await _ensure_column(conn, "sensory_snapshots", "network_rx_bytes_per_sec", "REAL")
        await _ensure_column(conn, "sensory_snapshots", "network_tx_bytes_per_sec", "REAL")
        await _ensure_column(conn, "sensory_snapshots", "sample_interval_seconds", "REAL")
        await _normalize_article_memories(conn)
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


async def _normalize_article_memories(conn: aiosqlite.Connection) -> None:
    async with conn.execute(
        """
        SELECT id, persona_id, content, summary, tags, created_at
        FROM memories
        WHERE source = 'article'
        """
    ) as cursor:
        rows = await cursor.fetchall()

    for memory_id, persona_id, content, summary, tags, created_at in rows:
        title = _extract_article_title(content)
        post = await _find_matching_post(conn, persona_id, title=title, summary=summary or "", created_at=created_at)
        summary_text = ((post["summary"] if post else summary) or title)[:180]
        body_source = post["content_markdown"] if post else content
        published_at = (post["published_at"] if post else None) or created_at
        normalized_content = _build_article_memory_content(
            title=(post["title"] if post else title) or title,
            published_at=published_at,
            summary=summary_text,
            body=body_source,
        )
        normalized_tags = _normalize_article_tags(tags, post["id"] if post else None)
        if normalized_content != content or normalized_tags != (tags or "[]") or summary_text != (summary or ""):
            await conn.execute(
                """
                UPDATE memories
                SET content = ?, summary = ?, tags = ?
                WHERE id = ?
                """,
                (normalized_content, summary_text, normalized_tags, memory_id),
            )


async def _find_matching_post(
    conn: aiosqlite.Connection,
    persona_id: int,
    *,
    title: str,
    summary: str,
    created_at: str,
) -> dict[str, object] | None:
    async with conn.execute(
        """
        SELECT id, title, content_markdown, summary, published_at, created_at
        FROM posts
        WHERE persona_id = ?
        ORDER BY published_at DESC, created_at DESC, id DESC
        """,
        (persona_id,),
    ) as cursor:
        rows = await cursor.fetchall()
    if not rows:
        return None

    summary_text = summary or ""
    best_row: tuple | None = None
    best_score = 0
    for row in rows:
        row_id, row_title, row_content, row_summary, row_published_at, row_created_at = row
        score = 0
        row_title = row_title or ""
        row_summary = row_summary or ""
        row_published_at = row_published_at or ""
        row_created_at = row_created_at or ""

        if title and row_title == title:
            score += 5
        if created_at and created_at in {row_published_at, row_created_at}:
            score += 4
        if summary_text and (summary_text.startswith(row_summary) or row_summary.startswith(summary_text)):
            score += 3
        if title and row_content and title in row_content:
            score += 1

        if score > best_score:
            best_score = score
            best_row = row

    if best_row is None or best_score == 0:
        return None
    return {
        "id": best_row[0],
        "title": best_row[1] or "",
        "content_markdown": best_row[2] or "",
        "summary": best_row[3] or "",
        "published_at": best_row[4] or best_row[5] or "",
    }


def _extract_article_title(content: str) -> str:
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("标题："):
            return line.split("：", 1)[1].strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return ""


def _extract_article_body_lines(body: str) -> list[str]:
    lines: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if any(
            line.startswith(prefix)
            for prefix in ("标题：", "发布时间：", "摘要：", "开场动作：", "收束状态：", "用途：")
        ):
            continue
        lines.append(line)
    return lines


def _build_article_memory_content(*, title: str, published_at: str, summary: str, body: str) -> str:
    lines = _extract_article_body_lines(body)
    opening = lines[0][:48] if lines else (summary or title)[:48]
    closing = lines[-1][:48] if lines else opening
    return "\n".join(
        [
            f"标题：{title}",
            f"发布时间：{published_at}",
            f"摘要：{summary[:180]}",
            f"开场动作：{opening}",
            f"收束状态：{closing}",
            "用途：用于保持长期叙事连续性，但新稿不得直接复写上述场景、动作或措辞。",
        ]
    ).strip()


def _normalize_article_tags(tags: str, post_id: int | None) -> str:
    try:
        raw_tags = json.loads(tags or "[]")
    except json.JSONDecodeError:
        raw_tags = []
    if not isinstance(raw_tags, list):
        raw_tags = []

    normalized: list[str] = []
    for item in raw_tags:
        tag = str(item).strip()
        if not tag or tag.startswith("post:") or tag in normalized:
            continue
        normalized.append(tag)
    if "article" in normalized:
        normalized.remove("article")
    normalized.insert(0, "article")
    if post_id is not None:
        normalized.append(f"post:{post_id}")
    return json.dumps(normalized, ensure_ascii=False)
