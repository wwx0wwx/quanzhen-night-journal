from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import Settings
from backend.models import Memory, Persona, Post, SystemConfig
from backend.utils.serde import json_dumps
from backend.utils.slug import slugify
from backend.utils.time import utcnow_iso


def _parse_markdown(raw: str) -> tuple[dict, str]:
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            front: dict[str, str] = {}
            for line in parts[1].splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    front[key.strip()] = value.strip().strip('"')
            return front, parts[2].strip()
    return {}, raw.strip()


async def import_legacy_assets(db: AsyncSession, settings: Settings) -> dict:
    marker = await db.get(SystemConfig, "migration.legacy_imported")
    if marker and marker.value == "1":
        return {"posts": 0, "memories": 0}

    default_persona = await db.scalar(select(Persona).where(Persona.is_default == 1))
    persona_id = default_persona.id if default_persona else None

    imported_posts = 0
    for folder, status in ((settings.seed_content_path / "posts", "published"), (settings.seed_draft_path, "pending_review")):
        if not folder.exists():
            continue
        for file in sorted(folder.glob("*.md")):
            slug = file.stem
            exists = await db.scalar(select(Post).where(Post.slug == slug))
            if exists:
                continue
            front, body = _parse_markdown(file.read_text(encoding="utf-8"))
            post = Post(
                title=front.get("title", slug),
                slug=slug,
                front_matter=json_dumps(front),
                content_markdown=body,
                summary=front.get("description", body[:120]),
                status=status,
                persona_id=persona_id,
                task_id=None,
                published_at=front.get("date") if status == "published" else None,
                revision=1,
                publish_target="hugo",
                digital_stamp=None,
                review_info=json_dumps({}),
                created_at=front.get("date", utcnow_iso()),
                updated_at=utcnow_iso(),
            )
            db.add(post)
            imported_posts += 1

    imported_memories = 0
    anchors = settings.automation_path / "memory_anchors.json"
    recent = settings.automation_path / "recent_memories.json"
    if persona_id and anchors.exists():
        import json

        for item in json.loads(anchors.read_text(encoding="utf-8")):
            content = item.get("summary") or item.get("content") or str(item)
            db.add(
                Memory(
                    persona_id=persona_id,
                    level="L0",
                    content=content,
                    summary=content[:120],
                    tags=json_dumps(["legacy_anchor"]),
                    source="import",
                    weight=1.5,
                    time_range_start=None,
                    time_range_end=None,
                    review_status="promoted",
                    decay_strategy="standard",
                    is_core=1,
                    created_at=utcnow_iso(),
                    last_accessed_at=None,
                )
            )
            imported_memories += 1

    if persona_id and recent.exists():
        import json

        for item in json.loads(recent.read_text(encoding="utf-8")):
            content = item.get("summary") or item.get("title") or str(item)
            db.add(
                Memory(
                    persona_id=persona_id,
                    level="L2",
                    content=content,
                    summary=content[:120],
                    tags=json_dumps(["legacy_recent"]),
                    source="import",
                    weight=1.0,
                    time_range_start=None,
                    time_range_end=None,
                    review_status="reviewed",
                    decay_strategy="standard",
                    is_core=0,
                    created_at=item.get("at", utcnow_iso()),
                    last_accessed_at=None,
                )
            )
            imported_memories += 1

    if marker is None:
        marker = SystemConfig(
            key="migration.legacy_imported",
            value="1",
            encrypted=0,
            category="system",
            updated_at=utcnow_iso(),
        )
        db.add(marker)
    else:
        marker.value = "1"

    await db.commit()
    return {"posts": imported_posts, "memories": imported_memories}
