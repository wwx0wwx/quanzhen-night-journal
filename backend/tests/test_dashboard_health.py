from __future__ import annotations

import httpx

from backend.adapters.llm_adapter import LLMAdapter


def test_dashboard_surfaces_recent_failure_reason(monkeypatch, authed_client):
    async def bad_chat(self, **_kwargs):  # noqa: ANN001
        return ("?" * 80, {"prompt_tokens": 12, "completion_tokens": 80}, 5)

    monkeypatch.setattr(LLMAdapter, "chat", bad_chat)

    config = authed_client.put(
        "/api/config",
        json={"items": [{"key": "qa.max_retries", "value": "1", "category": "qa"}]},
    )
    assert config.status_code == 200

    response = authed_client.post(
        "/api/tasks/trigger",
        json={"trigger_source": "manual", "semantic_hint": "probe invalid output", "payload": {"kind": "manual"}},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "failed"

    dashboard = authed_client.get("/api/dashboard")
    assert dashboard.status_code == 200
    data = dashboard.json()["data"]
    assert data["recent_tasks"][0]["error_code"] == "invalid_model_output"
    assert data["risk_overview"]["failed"] >= 1
    assert any(item["label"] == "invalid_model_output" for item in data["attention_items"])


def test_system_health_reports_uninitialized_and_missing_providers(client):
    response = client.get("/api/health/system")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "degraded"
    assert data["checks"]["api"]["status"] == "ok"
    assert data["checks"]["database"]["status"] == "ok"
    assert data["checks"]["setup"]["initialized"] is False
    assert data["checks"]["llm"]["configured"] is False
    assert data["checks"]["embedding"]["configured"] is False


def test_system_health_reports_ok_after_setup_and_provider_config(authed_client):
    update = authed_client.put(
        "/api/config",
        json={
            "items": [
                {"key": "llm.base_url", "value": "https://api.example.com/v1", "category": "llm"},
                {"key": "llm.api_key", "value": "live-llm-key", "category": "llm"},
                {"key": "llm.model_id", "value": "qwen-max", "category": "llm"},
                {"key": "embedding.base_url", "value": "https://api.example.com/v1", "category": "embedding"},
                {"key": "embedding.api_key", "value": "live-embedding-key", "category": "embedding"},
                {"key": "embedding.model_id", "value": "text-embedding-3-large", "category": "embedding"},
            ]
        },
    )
    assert update.status_code == 200

    response = authed_client.get("/api/health/system")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "ok"
    assert data["checks"]["setup"]["initialized"] is True
    assert data["checks"]["llm"]["configured"] is True
    assert data["checks"]["embedding"]["configured"] is True
    assert data["checks"]["scheduler"]["running"] is True


def test_system_health_marks_provider_probe_5xx_as_warning(monkeypatch, authed_client):
    class FakeClient:
        def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):  # noqa: ANN001
            return False

        async def get(self, url, **_kwargs):  # noqa: ANN001, ANN003
            request = httpx.Request("GET", url)
            return httpx.Response(503, request=request)

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)

    update = authed_client.put(
        "/api/config",
        json={
            "items": [
                {"key": "llm.base_url", "value": "https://api.example.com/v1", "category": "llm"},
                {"key": "llm.api_key", "value": "live-llm-key", "category": "llm"},
                {"key": "llm.model_id", "value": "qwen-max", "category": "llm"},
            ]
        },
    )
    assert update.status_code == 200

    response = authed_client.get("/api/health/system?probe_external=true")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "degraded"
    assert data["checks"]["llm"]["status"] == "warning"
    assert data["checks"]["llm"]["reachability"] == {
        "status": "error",
        "http_status": 503,
        "endpoint": "/models",
        "detail": "provider_probe_failed",
    }


def test_system_health_marks_provider_probe_auth_failure_as_warning(monkeypatch, authed_client):
    class FakeClient:
        def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):  # noqa: ANN001
            return False

        async def get(self, url, **_kwargs):  # noqa: ANN001, ANN003
            request = httpx.Request("GET", url)
            return httpx.Response(401, request=request)

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)

    update = authed_client.put(
        "/api/config",
        json={
            "items": [
                {"key": "llm.base_url", "value": "https://api.example.com/v1", "category": "llm"},
                {"key": "llm.api_key", "value": "bad-llm-key", "category": "llm"},
                {"key": "llm.model_id", "value": "qwen-max", "category": "llm"},
            ]
        },
    )
    assert update.status_code == 200

    response = authed_client.get("/api/health/system?probe_external=true")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "degraded"
    assert data["checks"]["llm"]["status"] == "warning"
    assert data["checks"]["llm"]["reachability"] == {
        "status": "error",
        "http_status": 401,
        "endpoint": "/models",
        "detail": "auth_failed",
    }
