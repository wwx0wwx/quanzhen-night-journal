from __future__ import annotations

import asyncio

from sqlalchemy import select

from backend.database import get_sessionmaker
from backend.models import Event, GenerationTask, Persona, SystemConfig, User
from backend.utils.audit import log_audit


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
    default_persona = setup.json()["data"]["default_persona"]
    assert default_persona["name"] == "全真"
    assert "王爷" in default_persona["identity_setting"]
    assert "武侠" in default_persona["worldview_setting"]
    assert any("不要让全真真正实施伤害王爷或姐姐" in item for item in default_persona["taboos"])

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


def test_audit_exposes_processed_event_for_task_logs(authed_client):
    normalized_semantic = "雨声被机柜冷光磨得更薄。"

    async def _seed() -> None:
        async with get_sessionmaker()() as db:
            persona = await db.scalar(select(Persona).where(Persona.is_default == 1))
            assert persona is not None

            task = GenerationTask(
                trigger_source="manual_test",
                event_id=None,
                persona_id=persona.id,
                context_snapshot="{}",
                memory_hits="[]",
                prompt_summary="{}",
                qa_result="{}",
                started_at="2026-04-15T00:00:00+00:00",
            )
            db.add(task)
            await db.flush()

            event = Event(
                event_type="manual_test",
                source="pytest",
                raw_payload="{}",
                normalized_semantic=normalized_semantic,
                auth_status="not_required",
                cooldown_status="ready",
                created_at="2026-04-15T00:00:01+00:00",
                task_id=task.id,
            )
            db.add(event)
            await db.flush()

            task.event_id = event.id
            await log_audit(
                db,
                "system",
                "task.status_change",
                "task",
                str(task.id),
                {"to": "queued"},
            )
            await db.commit()

    asyncio.run(_seed())

    audit = authed_client.get("/api/audit", params={"action": "task.status_change"})
    assert audit.status_code == 200
    items = audit.json()["data"]["items"]
    assert any(item["processed_event"] == normalized_semantic for item in items)
    assert any(item["display_action"] == "任务状态变更" for item in items)
    assert any(item["display_target"].startswith("写作任务 #") for item in items)
    assert any(item["event_mapping"] == normalized_semantic for item in items)
