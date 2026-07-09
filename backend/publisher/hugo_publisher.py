from __future__ import annotations

import asyncio
import json
import logging

import aiofiles

from backend.config import Settings, get_settings
from backend.models import Post
from backend.publisher.base import PublisherAdapter, PublishResult
from backend.utils.metrics import METRICS
from backend.utils.post_content import is_generic_title, normalize_title
from backend.utils.time import utcnow_iso

logger = logging.getLogger(__name__)

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

            signal = (post.updated_at or utcnow_iso()).strip() or utcnow_iso()
            self.settings.build_signal_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(self.settings.build_signal_path, "w", encoding="utf-8") as handle:
                await handle.write(signal)

            METRICS.incr("hugo.publish_requests")
            METRICS.note_event("hugo.last_signal", signal)
            build_ok, detail = await self._wait_for_build(expected_signal=signal, timeout=40)
            if not build_ok:
                METRICS.incr("hugo.publish_failures")
                return PublishResult(success=False, detail=detail)
            METRICS.incr("hugo.publish_success")
            return PublishResult(success=True, url=f"/posts/{post.slug}/", detail=str(filepath))

    async def unpublish(self, post: Post) -> None:
        async with PUBLISH_LOCK:
            filepath = self.settings.hugo_post_path / f"{post.slug}.md"
            if filepath.exists():
                filepath.unlink()
            signal = (post.updated_at or utcnow_iso()).strip() or utcnow_iso()
            async with aiofiles.open(self.settings.build_signal_path, "w", encoding="utf-8") as handle:
                await handle.write(signal)
            await self._wait_for_build(expected_signal=signal, timeout=40)

    async def health_check(self) -> bool:
        return self.settings.hugo_post_path.exists()

    async def _wait_for_build(self, *, expected_signal: str, timeout: int = 60) -> tuple[bool, str]:
        """Wait until build_status refers to this exact signal.

        This prevents accepting a stale status=ok from a previous build.
        """
        expected_signal = expected_signal.strip()
        for _ in range(timeout):
            if self.settings.build_status_path.exists():
                try:
                    payload = json.loads(self.settings.build_status_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    payload = {}
                status = str(payload.get("status", "")).strip().lower()
                signal = str(payload.get("signal", "")).strip()
                if signal == expected_signal:
                    if status == "ok":
                        return True, ""
                    if status == "error":
                        return False, str(payload.get("error", "hugo_build_failed"))
                    # running / unknown for this signal — keep waiting
                # Ignore status for other signals (stale ok from previous builds).
            await asyncio.sleep(1)
        logger.warning("hugo build timeout expected_signal=%s", expected_signal)
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
