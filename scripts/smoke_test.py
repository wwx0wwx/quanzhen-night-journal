from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


ADMIN_BASE = env("QZ_ADMIN_BASE_URL", "http://127.0.0.1:5210").rstrip("/")
BLOG_URL = env("QZ_BLOG_URL")
USERNAME = env("QZ_USERNAME", "admin")
PASSWORD = env("QZ_PASSWORD")
REQUIRE_AUTH = env("QZ_REQUIRE_AUTH", "1") != "0"
SKIP_ADMIN_ENTRY = env("QZ_SKIP_ADMIN_ENTRY", "0") == "1"
SKIP_BLOG_ENTRY = env("QZ_SKIP_BLOG_ENTRY", "0") == "1"


cookie_jar = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))


def request(url: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, str]:
    body = None
    headers = {
        "Accept": "application/json, text/html;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) QuanzhenSmoke/1.0",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with opener.open(req, timeout=20) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        return exc.code, body_text


def assert_ok(condition: bool, label: str, detail: str = "") -> None:
    if not condition:
        raise RuntimeError(f"{label} failed{': ' + detail if detail else ''}")
    print(f"[PASS] {label}")


def run() -> int:
    ping_status, ping_body = request(f"{ADMIN_BASE}/api/health/ping")
    assert_ok(ping_status == 200 and '"status":"ok"' in ping_body.replace(" ", ""), "health ping")

    system_status, system_body = request(f"{ADMIN_BASE}/api/health/system")
    assert_ok(system_status == 200 and '"checks"' in system_body, "system health")

    if SKIP_ADMIN_ENTRY:
        print("[SKIP] admin entry (QZ_SKIP_ADMIN_ENTRY=1)")
    else:
        admin_status, admin_body = request(f"{ADMIN_BASE}/admin/")
        assert_ok(admin_status == 200 and "<html" in admin_body.lower(), "admin entry")

    if BLOG_URL and not SKIP_BLOG_ENTRY:
        blog_status, blog_body = request(BLOG_URL)
        assert_ok(blog_status == 200 and "<html" in blog_body.lower(), "blog entry")
    else:
        reason = "QZ_SKIP_BLOG_ENTRY=1" if SKIP_BLOG_ENTRY else "QZ_BLOG_URL not set"
        print(f"[SKIP] blog entry ({reason})")

    if REQUIRE_AUTH:
        if not PASSWORD:
            raise RuntimeError("QZ_PASSWORD is required when QZ_REQUIRE_AUTH=1")

        login_status, login_body = request(
            f"{ADMIN_BASE}/api/auth/login",
            method="POST",
            payload={"username": USERNAME, "password": PASSWORD},
        )
        assert_ok(login_status == 200 and '"is_logged_in":true' in login_body.replace(" ", "").lower(), "auth login")

        dashboard_status, dashboard_body = request(f"{ADMIN_BASE}/api/dashboard")
        assert_ok(dashboard_status == 200 and '"recent_tasks"' in dashboard_body, "dashboard api")

        posts_status, posts_body = request(f"{ADMIN_BASE}/api/posts")
        assert_ok(posts_status == 200 and '"items"' in posts_body, "posts api")
    else:
        print("[SKIP] authenticated checks (QZ_REQUIRE_AUTH=0)")

    print("[DONE] smoke test passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
