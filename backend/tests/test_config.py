from __future__ import annotations

import asyncio

from backend.api.deps import get_encryptor
from backend.config import DEFAULT_JWT_SECRET, Settings, get_settings
from backend.database import get_sessionmaker
from backend.engine.config_store import ConfigStore
from backend.engine.site_runtime import SiteRuntimeManager
from backend.models import SystemConfig


def _read_secret_state(key: str) -> tuple[str | None, int]:
    async def _inner() -> tuple[str | None, int]:
        session_factory = get_sessionmaker()
        async with session_factory() as db:
            encryptor = await get_encryptor(db)
            store = ConfigStore(db, encryptor)
            entry = await db.get(SystemConfig, key)
            value = await store.get(key)
            return value, int(entry.encrypted if entry else 0)

    return asyncio.run(_inner())


def test_config_secret_updates_stay_encrypted_and_masked(authed_client):
    update = authed_client.put(
        "/api/config",
        json={
            "items": [
                {"key": "llm.api_key", "value": "secret-live-key"},
                {"key": "llm.base_url", "value": ""},
                {"key": "llm.model_id", "value": ""},
            ]
        },
    )
    assert update.status_code == 200

    config = authed_client.get("/api/config")
    assert config.status_code == 200
    assert config.json()["data"]["llm.api_key"]["value"] == "******"

    secret_value, encrypted = _read_secret_state("llm.api_key")
    assert secret_value == "secret-live-key"
    assert encrypted == 1

    second_update = authed_client.put(
        "/api/config",
        json={"items": [{"key": "llm.api_key", "value": "******"}, {"key": "site.title", "value": "新标题"}]},
    )
    assert second_update.status_code == 200

    secret_value, encrypted = _read_secret_state("llm.api_key")
    assert secret_value == "secret-live-key"
    assert encrypted == 1

    probe = authed_client.post(
        "/api/config/test-llm",
        json={"base_url": "", "api_key": "******", "model_id": ""},
    )
    assert probe.status_code == 200
    assert probe.json()["data"]["reply"]


def test_domain_status_reports_ip_mode(authed_client):
    response = authed_client.get("/api/config/status/domain")
    assert response.status_code == 200
    assert response.json()["data"]["enabled"] is False
    assert "IP 模式" in response.json()["data"]["reason"]


def test_schedule_config_update_does_not_fail_with_scheduler_lock(authed_client):
    response = authed_client.put(
        "/api/config",
        json={
            "items": [
                {"key": "schedule.days_per_cycle", "value": "3", "category": "schedule"},
                {"key": "schedule.posts_per_cycle", "value": "2", "category": "schedule"},
                {"key": "schedule.publish_time", "value": "21:02", "category": "schedule"},
                {"key": "schedule.review_cron", "value": "0 2 * * 0", "category": "schedule"},
                {"key": "schedule.decay_cron", "value": "0 3 * * *", "category": "schedule"},
                {"key": "schedule.sample_interval_minutes", "value": "7", "category": "schedule"},
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["updated"] == 6


def test_cloudflare_proxy_domain_can_be_allowed(monkeypatch, authed_client):
    async def _inner() -> None:
        session_factory = get_sessionmaker()
        async with session_factory() as db:
            encryptor = await get_encryptor(db)
            store = ConfigStore(db, encryptor)
            await store.set("site.domain", "iuaa.de", category="site")
            settings = get_settings().model_copy(update={"allow_cloudflare_proxy_domain": True})
            manager = SiteRuntimeManager(store, settings=settings)
            monkeypatch.setattr(
                manager,
                "_resolve_domain_ips",
                lambda domain: asyncio.sleep(0, result=["104.21.5.181", "172.67.133.179", "2606:4700:3033::6815:5b5"]),
            )
            monkeypatch.setattr(manager, "_candidate_server_ips", lambda: {"38.76.204.233"})
            result = await manager.inspect_domain("iuaa.de")
            assert result.enabled is True
            assert "Cloudflare" in result.reason

    asyncio.run(_inner())


def test_domain_caddyfile_only_serves_blog_on_domain():
    settings = get_settings().model_copy(update={"acme_email": "ops@example.com"})
    manager = SiteRuntimeManager(config_store=None, settings=settings)  # type: ignore[arg-type]

    rendered = manager._render_caddyfile("iuaa.de")

    assert "(qz_console)" in rendered
    assert "(qz_blog)" in rendered
    assert "redir /admin /admin/ 308" in rendered
    assert "handle_path /admin/*" in rendered
    assert 'header Cache-Control "no-store"' in rendered
    assert "@console_root path /" in rendered
    assert "redir @console_root /admin/ 308" in rendered
    assert "respond 404" in rendered
    assert ":5210 {\n    import qz_console\n}" in rendered
    assert "iuaa.de {\n    import qz_blog\n}" in rendered
    assert "respond @blocked 404" in rendered


def test_production_requires_custom_jwt_secret():
    settings = Settings(_env_file=None, ENVIRONMENT="production", JWT_SECRET=DEFAULT_JWT_SECRET)
    try:
        settings.validate_runtime()
    except RuntimeError as exc:
        assert "JWT_SECRET" in str(exc)
    else:
        raise AssertionError("production runtime should reject the default JWT_SECRET")


def test_production_allows_custom_jwt_secret():
    settings = Settings(_env_file=None, ENVIRONMENT="production", JWT_SECRET="custom-prod-secret-123456789")
    settings.validate_runtime()
