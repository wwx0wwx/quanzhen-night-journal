from __future__ import annotations

import asyncio
import ipaddress
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from backend.engine.site_runtime import CLOUDFLARE_NETWORKS
from backend.utils.response import error


@dataclass(frozen=True, slots=True)
class RateLimitRule:
    limit: int
    window_seconds: int


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, key: str, bucket: str, rule: RateLimitRule) -> tuple[bool, int]:
        now = time.monotonic()
        threshold = now - rule.window_seconds
        async with self._lock:
            window = self._events[(bucket, key)]
            while window and window[0] <= threshold:
                window.popleft()
            if len(window) >= rule.limit:
                retry_after = max(1, int(rule.window_seconds - (now - window[0])))
                return False, retry_after
            window.append(now)
        return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    DEFAULT_RULE = RateLimitRule(limit=240, window_seconds=60)
    RULES: tuple[tuple[str, RateLimitRule], ...] = (
        ("/api/auth/login", RateLimitRule(limit=10, window_seconds=300)),
        ("/api/setup/complete", RateLimitRule(limit=5, window_seconds=3600)),
        ("/api/webhook", RateLimitRule(limit=30, window_seconds=60)),
        ("/api/config/test-llm", RateLimitRule(limit=20, window_seconds=60)),
        ("/api/config/test-embedding", RateLimitRule(limit=20, window_seconds=60)),
    )

    def __init__(self, app) -> None:  # noqa: ANN001
        super().__init__(app)
        self.limiter = SlidingWindowLimiter()

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        if request.method == "OPTIONS" or not request.url.path.startswith("/api/"):
            return await call_next(request)

        key = self._client_key(request)
        bucket, rule = self._resolve_rule(request.url.path)
        allowed, retry_after = await self.limiter.check(key, bucket, rule)
        if not allowed:
            response = error(
                4291,
                "rate_limit_exceeded",
                {"bucket": bucket, "retry_after_seconds": retry_after},
                status_code=429,
            )
            response.headers["Retry-After"] = str(retry_after)
            return response

        return await call_next(request)

    def _resolve_rule(self, path: str) -> tuple[str, RateLimitRule]:
        for prefix, rule in self.RULES:
            if path.startswith(prefix):
                return prefix, rule
        return "/api", self.DEFAULT_RULE

    def _client_key(self, request: Request) -> str:
        test_scope = os.getenv("PYTEST_CURRENT_TEST", "").split(" ")[0]
        peer_ip = (request.client.host if request.client else "") or ""
        is_trusted_proxy = self._is_cloudflare_ip(peer_ip)
        if is_trusted_proxy:
            cf_ip = request.headers.get("cf-connecting-ip", "").strip()
            if cf_ip:
                key = cf_ip.split(",")[0].strip()
                return f"{test_scope}:{key}" if test_scope else key
        for header in ("x-real-ip", "x-forwarded-for"):
            raw = request.headers.get(header, "").strip()
            if raw:
                key = raw.split(",")[0].strip()
                return f"{test_scope}:{key}" if test_scope else key
        if peer_ip:
            return f"{test_scope}:{peer_ip}" if test_scope else peer_ip
        return f"{test_scope}:unknown" if test_scope else "unknown"

    @staticmethod
    def _is_cloudflare_ip(ip_str: str) -> bool:
        if not ip_str:
            return False
        try:
            addr = ipaddress.ip_address(ip_str)
            return any(addr in net for net in CLOUDFLARE_NETWORKS)
        except ValueError:
            return False
