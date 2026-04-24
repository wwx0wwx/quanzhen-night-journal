"""Import seed blog posts from content/posts/ into the database.

Called during setup to give new users two starter posts (prologue + first diary).
"""

from __future__ import annotations

import logging
import shutil

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.models import Post
from backend.utils.serde import json_dumps
from backend.utils.time import utcnow_iso

logger = logging.getLogger(__name__)


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            front: dict[str, object] = {}
            for line in parts[1].splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    val = value.strip().strip('"')
                    if val.startswith("[") and val.endswith("]"):
                        import json

                        try:
                            val = json.loads(val)
                        except json.JSONDecodeError:
                            pass
                    front[key.strip()] = val
            return front, parts[2].strip()
    return {}, raw.strip()


async def create_seed_posts(db: AsyncSession, persona_id: int | None) -> int:
    settings = get_settings()
    seed_dir = settings.seed_content_path / "posts"
    if not seed_dir.exists():
        return 0

    imported = 0
    for md_file in sorted(seed_dir.glob("*.md")):
        slug = md_file.stem
        exists = await db.scalar(select(Post.id).where(Post.slug == slug))
        if exists:
            continue

        raw = md_file.read_text(encoding="utf-8")
        front, body = _parse_frontmatter(raw)

        tags = front.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]

        post = Post(
            title=front.get("title", slug),
            slug=slug,
            front_matter=json_dumps(front),
            content_markdown=body,
            summary=front.get("description", body[:120]),
            status="published",
            persona_id=persona_id,
            task_id=None,
            published_at=str(front["date"]) if "date" in front else utcnow_iso(),
            revision=1,
            publish_target="hugo",
            digital_stamp=None,
            review_info=json_dumps({}),
            created_at=str(front.get("date", utcnow_iso())),
            updated_at=utcnow_iso(),
        )
        db.add(post)
        imported += 1

        hugo_dest = settings.hugo_post_path / md_file.name
        hugo_dest.parent.mkdir(parents=True, exist_ok=True)
        if not hugo_dest.exists():
            shutil.copy2(md_file, hugo_dest)

    if imported:
        logger.info("imported %d seed post(s)", imported)
    return imported
