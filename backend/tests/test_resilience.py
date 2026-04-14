from __future__ import annotations

import asyncio

import httpx

from backend.adapters.llm_adapter import LLMAdapter
from backend.database import get_sessionmaker
from backend.engine.persona_engine import PersonaEngine
from backend.models import Persona
from backend.utils.time import utcnow_iso


def test_health_root_returns_summary(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["checks"]["api"]["status"] == "ok"
    assert data["checks"]["database"]["status"] == "ok"
    assert "disk" in data["checks"]


def test_login_is_rate_limited(client):
    setup = client.post(
        "/api/setup/complete",
        json={
            "new_password": "quanzhen123",
            "site_title": "全真夜记",
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

    for _ in range(10):
        response = client.post("/api/auth/login", json={"username": "admin", "password": "quanzhen123"})
        assert response.status_code == 200

    blocked = client.post("/api/auth/login", json={"username": "admin", "password": "quanzhen123"})
    assert blocked.status_code == 429
    assert blocked.json()["message"] == "rate_limit_exceeded"


def test_persona_creation_rejects_corrupted_text(authed_client):
    response = authed_client.post(
        "/api/personas",
        json={
            "name": "??",
            "description": "??????????",
            "is_active": True,
            "is_default": False,
            "identity_setting": "????????",
            "worldview_setting": "",
            "language_style": "",
            "taboos": [],
            "sensory_lexicon": {},
            "structure_preference": "medium",
            "expression_intensity": "moderate",
            "stability_params": {"temperature_base": 0.7, "temperature_range": [0.3, 1.0]},
        },
    )

    assert response.status_code == 422


def test_corrupted_persona_can_be_repaired(client):
    async def exercise() -> None:
        session_factory = get_sessionmaker()
        async with session_factory() as db:
            db.add(
                Persona(
                    name="??",
                    description="??????????",
                    is_active=1,
                    is_default=0,
                    identity_setting="????????",
                    worldview_setting="????????",
                    language_style="??",
                    taboos="[]",
                    sensory_lexicon="{}",
                    structure_preference="medium",
                    expression_intensity="moderate",
                    stability_params="{}",
                    created_at=utcnow_iso(),
                    updated_at=utcnow_iso(),
                )
            )
            await db.commit()

        async with session_factory() as db:
            repaired = await PersonaEngine(db).repair_corrupted_personas()
            await db.commit()
            rows = await db.get(Persona, max(repaired))
            assert repaired
            assert rows.name.startswith("待修复人格")
            assert rows.is_active == 0

    asyncio.run(exercise())


def test_llm_adapter_retries_timeout(monkeypatch):
    calls = {"count": 0}

    class FakeClient:
        def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):  # noqa: ANN001
            return False

        async def post(self, *args, **kwargs):  # noqa: ANN002, ANN003
            calls["count"] += 1
            if calls["count"] < 3:
                raise httpx.ReadTimeout("timed out")
            request = httpx.Request("POST", "https://api.example.com/v1/chat/completions")
            return httpx.Response(
                200,
                request=request,
                json={
                    "choices": [{"message": {"content": "ok"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            )

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)

    async def exercise() -> None:
        text, usage, _ = await LLMAdapter().chat(
            base_url="https://api.example.com/v1",
            api_key="token",
            model_id="model",
            messages=[{"role": "user", "content": "ping"}],
        )
        assert text == "ok"
        assert usage["completion_tokens"] == 1

    asyncio.run(exercise())
    assert calls["count"] == 3
