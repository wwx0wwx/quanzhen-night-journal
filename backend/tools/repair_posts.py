from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass

import aiofiles
from sqlalchemy import select

from backend.config import get_settings
from backend.database import get_sessionmaker
from backend.models import Post, SystemConfig
from backend.publisher.hugo_publisher import HugoPublisher
from backend.utils.post_content import (
    derive_summary,
    extract_title,
    is_generic_title,
    normalize_title,
)
from backend.utils.slug import is_placeholder_slug, slugify
from backend.utils.time import utcnow_iso


@dataclass(slots=True)
class RepairResult:
    scanned: int = 0
    changed: int = 0
    archived_hidden: int = 0
    slug_changed: int = 0


def _desired_title(post: Post, site_title: str) -> str:
    current_title = normalize_title(post.title, max_length=64)
    invalid_titles = {site_title, "全真夜记", "夜记", "无题", "未命名夜记"}
    extracted = normalize_title(
        extract_title(post.content_markdown, invalid_titles=invalid_titles),
        max_length=64,
    )
    if post.status == "archived" and "损坏稿件已隔离" in (post.title or ""):
        return "异常稿件（已归档）"
    if current_title and not is_generic_title(current_title, site_title=site_title):
        return current_title
    return extracted or f"夜记 {post.id}"


def _desired_summary(post: Post, title: str, *, force_refresh: bool = False) -> str:
    if post.status == "archived" and "损坏稿件已隔离" in (post.title or ""):
        return "内容异常，已从前台归档。"
    summary = normalize_title(post.summary, max_length=180)
    if summary and summary != title and not force_refresh:
        return summary
    return derive_summary(post.content_markdown, title=title, max_length=180) or title


def _desired_slug(post: Post, title: str) -> str:
    if post.status == "archived":
        return post.slug
    source = "" if is_placeholder_slug(post.slug) else post.slug
    return slugify(source or title, fallback_prefix="post")


async def _ensure_unique_slug(db, post_id: int, desired_slug: str, reserved_slugs: set[str]) -> str:
    candidate = desired_slug
    suffix = 2
    while True:
        if candidate in reserved_slugs:
            candidate = f"{desired_slug}-{suffix}"
            suffix += 1
            continue
        row = await db.scalar(select(Post.id).where(Post.slug == candidate, Post.id != post_id))
        if row is None:
            return candidate
        candidate = f"{desired_slug}-{suffix}"
        suffix += 1


async def _rewrite_published_file(post: Post, old_slug: str | None) -> None:
    settings = get_settings()
    publisher = HugoPublisher(settings)
    new_path = settings.hugo_post_path / f"{post.slug}.md"
    new_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(new_path, "w", encoding="utf-8") as handle:
        await handle.write(publisher._render_hugo_markdown(post))

    if old_slug and old_slug != post.slug:
        old_path = settings.hugo_post_path / f"{old_slug}.md"
        if old_path.exists():
            old_path.unlink()


async def repair_posts(*, apply_changes: bool) -> RepairResult:
    result = RepairResult()
    session_factory = get_sessionmaker()
    settings = get_settings()

    async with session_factory() as db:
        site_title = await db.scalar(select(SystemConfig.value).where(SystemConfig.key == "site.title")) or "全真夜记"
        posts = list(await db.scalars(select(Post).order_by(Post.id.asc())))
        result.scanned = len(posts)
        reserved_slugs: set[str] = set()

        for post in posts:
            title = _desired_title(post, site_title)
            title_changed = post.title != title
            summary = _desired_summary(
                post,
                title,
                force_refresh=title_changed or is_generic_title(post.title, site_title=site_title),
            )
            slug = await _ensure_unique_slug(db, post.id, _desired_slug(post, title), reserved_slugs)
            old_slug = post.slug

            archived_file = settings.hugo_post_path / f"{post.slug}.md"
            changed = any(
                [
                    post.title != title,
                    post.summary != summary,
                    post.slug != slug,
                ]
            )

            if post.status == "archived" and archived_file.exists():
                changed = True

            if not changed:
                continue

            result.changed += 1
            if post.slug != slug:
                result.slug_changed += 1
            if post.status == "archived":
                result.archived_hidden += 1

            if not apply_changes:
                print(f"would-fix post#{post.id}: title={title!r} slug={old_slug!r}->{slug!r} status={post.status}")
                reserved_slugs.add(slug)
                continue

            post.title = title
            post.summary = summary
            post.slug = slug
            post.updated_at = utcnow_iso()

            if post.status == "published":
                await _rewrite_published_file(post, old_slug)
            elif archived_file.exists():
                archived_file.unlink()

            reserved_slugs.add(post.slug)

        if apply_changes:
            await db.commit()
            settings.build_signal_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(settings.build_signal_path, "w", encoding="utf-8") as handle:
                await handle.write(utcnow_iso())

    return result


async def main() -> None:
    parser = argparse.ArgumentParser(description="Repair historical post titles, summaries and slugs.")
    parser.add_argument("--apply", action="store_true", help="Persist changes instead of running in dry-run mode.")
    args = parser.parse_args()

    result = await repair_posts(apply_changes=args.apply)
    mode = "applied" if args.apply else "dry-run"
    print(
        f"{mode}: scanned={result.scanned} changed={result.changed} "
        f"slug_changed={result.slug_changed} archived_hidden={result.archived_hidden}"
    )


if __name__ == "__main__":
    asyncio.run(main())
