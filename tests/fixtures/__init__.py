from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FixtureSummary:
    automation_files: list[str]
    content_posts: list[str]
    draft_review: list[str]


def summarize_fixtures(base: Path) -> FixtureSummary:
    automation = sorted(p.name for p in (base / 'automation').glob('*') if p.is_file())
    content_posts = sorted(p.name for p in (base / 'content_posts').glob('*') if p.is_file())
    draft_review = sorted(p.name for p in (base / 'draft_review').glob('*') if p.is_file())
    return FixtureSummary(
        automation_files=automation,
        content_posts=content_posts,
        draft_review=draft_review,
    )
