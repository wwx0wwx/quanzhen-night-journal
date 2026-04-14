from __future__ import annotations

import httpx

from backend.config import get_settings


class CaddyAdapter:
    async def reload(self, config_text: str) -> bool:
        settings = get_settings()
        if not settings.caddy_reload_enabled:
            return False
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                settings.caddy_reload_url,
                content=config_text.encode("utf-8"),
                headers={"Content-Type": "text/caddyfile"},
            )
            response.raise_for_status()
        return True
