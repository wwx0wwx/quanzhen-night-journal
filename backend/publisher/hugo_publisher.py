from __future__ import annotations

import asyncio
import json

import aiofiles

from backend.config import Settings, get_settings
from backend.models import Post
from backend.publisher.base import PublisherAdapter, PublishResult
from backend.utils.post_content import is_generic_title, normalize_title

PUBLISH_LOCK = asyncio.Lock()


class HugoPublisher(PublisherAdapter):
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    async def publish(self, post: Post) -> PublishResult:
        async with PUBLISH_LOCK:
            filepath = self.settings.hugo_post_path / f"{post.slug}.md"
            filepath.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(filepath, "w", encoding="utf-8") as handle:
                await handle.write(self._render_hugo_markdown(post))

            self.settings.build_signal_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(self.settings.build_signal_path, "w", encoding="utf-8") as handle:
                await handle.write(post.updated_at)

            build_ok, detail = await self._wait_for_build(timeout=40)
            if not build_ok:
                return PublishResult(success=False, detail=detail)
            return PublishResult(success=True, url=f"/posts/{post.slug}/", detail=str(filepath))

    async def unpublish(self, post: Post) -> None:
        async with PUBLISH_LOCK:
            filepath = self.settings.hugo_post_path / f"{post.slug}.md"
            if filepath.exists():
                filepath.unlink()
            async with aiofiles.open(self.settings.build_signal_path, "w", encoding="utf-8") as handle:
                await handle.write(post.updated_at)

    async def health_check(self) -> bool:
        return self.settings.hugo_post_path.exists()

    async def _wait_for_build(self, timeout: int = 60) -> tuple[bool, str]:
        for _ in range(timeout):
            if self.settings.build_status_path.exists():
                try:
                    payload = json.loads(self.settings.build_status_path.read_text(encoding="utf-8"))
                    if payload.get("status") == "ok":
                        return True, ""
                    if payload.get("status") == "error":
                        return False, payload.get("error", "hugo_build_failed")
                except json.JSONDecodeError:
                    pass
            await asyncio.sleep(1)
        return False, "hugo_build_timeout"

    def _render_hugo_markdown(self, post: Post) -> str:
        front = json.loads(post.front_matter or "{}")
        front["title"] = post.title
        front["slug"] = post.slug
        front["summary"] = post.summary
        front["description"] = post.summary
        front["draft"] = False
        front.setdefault("date", post.published_at or post.created_at)
        lines = ["---"]
        for key, value in front.items():
            lines.append(f"{key}: {self._yaml_scalar(value)}")
        lines.append("---")
        lines.append("")
        lines.append(self._render_body(post))
        return "\n".join(lines).strip() + "\n"

    def _render_body(self, post: Post) -> str:
        content = post.content_markdown.lstrip()
        lines = content.splitlines()
        if lines:
            first_line = lines[0].strip()
            if first_line.startswith("#"):
                heading = normalize_title(first_line)
                if heading and (heading == normalize_title(post.title) or is_generic_title(heading)):
                    return "\n".join(lines[1:]).lstrip()
        return post.content_markdown

    def _yaml_scalar(self, value: object) -> str:
        if isinstance(value, list):
            return "[" + ", ".join(self._yaml_scalar(item) for item in value) + "]"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        text = str(value).replace('"', '\\"')
        return f'"{text}"'
