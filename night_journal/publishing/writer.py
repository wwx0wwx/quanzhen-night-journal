from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

UTC = timezone.utc


def build_markdown(
    title: str,
    description: str,
    category: str,
    body: str,
    now: datetime | None = None,
) -> tuple[str, str, str]:
    """
    Build Hugo-compatible Markdown content.
    Returns (markdown_text, now_str, slug).
    """
    if now is None:
        now = datetime.now(UTC).replace(microsecond=0)
    now_str = now.isoformat().replace('+00:00', 'Z')
    slug = now.strftime('%Y%m%d-%H%M%S') + '-night-note'
    md = (
        f'---\n'
        f'title: "{title}"\n'
        f'date: {now_str}\n'
        f'draft: false\n'
        f'tags: ["全真", "夜札", "{category}"]\n'
        f'author: "全真"\n'
        f'description: "{description}"\n'
        f'---\n\n'
        f'{body}\n'
    )
    return md, now_str, slug


def route_output_dir(
    overrides: dict,
    content_dir: Path,
    draft_review_dir: Path,
) -> Path:
    """
    Determine where to write the output file based on mode.
    auto → content_dir
    review-first / anything else → draft_review_dir
    """
    mode = overrides.get('mode', 'auto')
    if mode == 'auto':
        return content_dir
    return draft_review_dir


def write_post(
    title: str,
    description: str,
    category: str,
    body: str,
    overrides: dict,
    content_dir: Path,
    draft_review_dir: Path,
    now: datetime | None = None,
) -> tuple[Path, str, str]:
    """
    Build and write a Hugo Markdown post.
    Returns (path, now_str, slug).
    """
    md, now_str, slug = build_markdown(title, description, category, body, now)
    target_dir = route_output_dir(overrides, content_dir, draft_review_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f'{slug}.md'
    path.write_text(md, encoding='utf-8')
    return path, now_str, slug
