from __future__ import annotations

import asyncio

from sqlalchemy import select

from backend.database import get_sessionmaker
from backend.models import SystemConfig, User


def test_setup_and_login_flow(client):
    status = client.get("/api/setup/status")
    assert status.status_code == 200
    assert status.json()["data"]["system_initialized"] is False

    setup = client.post(
        "/api/setup/complete",
        json={
            "new_password": "quanzhen123",
            "site_title": "鍏ㄧ湡澶滆",
            "site_subtitle": "",
            "site_domain": "",
            "llm_base_url": "",
            "llm_api_key": "",
            "llm_model_id": "",
            "embedding_base_url": "",
            "embedding_api_key": "",
            "embedding_model_id": "",
        },
    )
    assert setup.status_code == 200
    assert setup.json()["data"]["system_initialized"] is True

    login = client.post("/api/auth/login", json={"username": "admin", "password": "quanzhen123"})
    assert login.status_code == 200
    assert login.json()["data"]["is_logged_in"] is True
    assert login.json()["data"]["is_initialized"] is True

    second_setup = client.post(
        "/api/setup/complete",
        json={
            "new_password": "anotherpass123",
            "site_title": "鍏ㄧ湡澶滆",
            "site_subtitle": "",
            "site_domain": "",
            "llm_base_url": "",
            "llm_api_key": "",
            "llm_model_id": "",
            "embedding_base_url": "",
            "embedding_api_key": "",
            "embedding_model_id": "",
        },
    )
    assert second_setup.status_code == 403

    auth_status = client.get("/api/auth/status")
    assert auth_status.json()["data"]["is_initialized"] is True
    assert auth_status.json()["data"]["system_initialized"] is True


def test_auth_status_uses_system_initialized_as_single_source(authed_client):
    async def _mutate() -> None:
        async with get_sessionmaker()() as db:
            admin = await db.scalar(select(User).where(User.username == "admin"))
            marker = await db.get(SystemConfig, "system.initialized")
            admin.is_initialized = 0
            marker.value = "1"
            await db.commit()

    asyncio.run(_mutate())

    status = authed_client.get("/api/auth/status")
    assert status.status_code == 200
    assert status.json()["data"]["is_initialized"] is True
    assert status.json()["data"]["system_initialized"] is True

    login = authed_client.post("/api/auth/login", json={"username": "admin", "password": "quanzhen123"})
    assert login.status_code == 200
    assert login.json()["data"]["is_initialized"] is True


def test_startup_self_heal_actions_are_audited(authed_client):
    audit = authed_client.get("/api/audit")
    assert audit.status_code == 200
    actions = {item["action"] for item in audit.json()["data"]["items"]}
    assert "system.ensure_seed_persona" in actions
    assert "system.apply_site_runtime" in actions
    assert any(action.startswith("system.") for action in actions)
