"""Lightweight CSRF mitigation for cookie-authenticated mutating API calls.

Rejects cross-site POSTs when Origin/Referer host is present and does not match
an allowed host (request host or configured site/CORS origins).
"""

from __future__ import annotations

from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from backend.config import get_settings
from backend.utils.response import error

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
# Public or bootstrap endpoints that may be called cross-origin without admin SPA origin.
EXEMPT_PREFIXES = (
    "/api/auth/login",
    "/api/auth/2fa",
    "/api/setup/",
    "/api/webhook",
    "/api/telemetry/",
    "/api/health/ping",
)


class CsrfOriginMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        if request.method in SAFE_METHODS:
            return await call_next(request)
        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)
        if any(path.startswith(prefix) for prefix in EXEMPT_PREFIXES):
            return await call_next(request)
        # Only enforce when a session cookie is present (cookie-auth CSRF surface).
        settings = get_settings()
        if not request.cookies.get(settings.cookie_name):
            return await call_next(request)

        origin = (request.headers.get("origin") or "").strip()
        referer = (request.headers.get("referer") or "").strip()
        candidate = origin or referer
        if not candidate:
            # Same-site navigations from some clients omit Origin; allow if no hint.
            return await call_next(request)

        if not self._is_allowed(candidate, request):
            return error(2001, "csrf_origin_rejected", status_code=403)
        return await call_next(request)

    def _is_allowed(self, candidate: str, request: Request) -> bool:
        host = (urlparse(candidate).netloc or "").lower()
        if not host:
            return False
        allowed: set[str] = set()
        if request.url.hostname:
            port = request.url.port
            if port and port not in (80, 443):
                allowed.add(f"{request.url.hostname.lower()}:{port}")
            allowed.add(request.url.hostname.lower())
        settings = get_settings()
        for raw in [settings.site_base_url, *(settings.cors_origins or "").split(",")]:
            raw = (raw or "").strip()
            if not raw:
                continue
            parsed = urlparse(raw if "://" in raw else f"http://{raw}")
            if parsed.netloc:
                allowed.add(parsed.netloc.lower())
        # localhost variants
        for item in list(allowed):
            if item.startswith("127.0.0.1"):
                allowed.add(item.replace("127.0.0.1", "localhost"))
            if item.startswith("localhost"):
                allowed.add(item.replace("localhost", "127.0.0.1"))
        return host in allowed
