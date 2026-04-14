from __future__ import annotations

import asyncio

import httpx
import pytest

from backend.adapters.llm_adapter import LLMAdapter
from backend.scheduler.jobs import scheduled_generation_job


def test_generation_trigger_publishes(authed_client):
    response = authed_client.post(
        "/api/tasks/trigger",
        json={"trigger_source": "manual", "semantic_hint": "write a short night note", "payload": {"kind": "manual"}},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "published"

    posts = authed_client.get("/api/posts")
    assert posts.json()["data"]["items"]
    assert posts.json()["data"]["items"][0]["status"] in {"published", "pending_review"}


def test_high_risk_task_waits_for_human_signoff(monkeypatch, authed_client):
    async def risky_chat(self, **_kwargs):  # noqa: ANN001
        return ("tonight drifts through the machine room and refuses to leave.", {"prompt_tokens": 12, "completion_tokens": 20}, 5)

    monkeypatch.setattr(LLMAdapter, "chat", risky_chat)

    config = authed_client.put(
        "/api/config",
        json={
            "items": [
                {"key": "qa.min_length", "value": "1", "category": "qa"},
                {"key": "qa.forbidden_words", "value": "[\"tonight\"]", "category": "qa"},
            ]
        },
    )
    assert config.status_code == 200

    response = authed_client.post(
        "/api/tasks/trigger",
        json={"trigger_source": "manual", "semantic_hint": "tonight prompt", "payload": {"kind": "manual"}},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "waiting_human_signoff"

    approve = authed_client.post(f"/api/tasks/{data['id']}/approve", json={"publish_immediately": True})
    assert approve.status_code == 200
    assert approve.json()["data"]["status"] == "published"

    task_detail = authed_client.get(f"/api/tasks/{data['id']}")
    assert task_detail.status_code == 200
    task_data = task_detail.json()["data"]
    assert task_data["qa_auto_passed"] is False
    assert task_data["human_approved"] is True
    assert task_data["final_publish_allowed"] is True
    assert task_data["publish_decision_path"] == "human_approved"

    post_detail = authed_client.get(f"/api/posts/{task_data['post_id']}")
    assert post_detail.status_code == 200
    post_data = post_detail.json()["data"]
    assert post_data["qa_auto_passed"] is False
    assert post_data["human_approved"] is True
    assert post_data["final_publish_allowed"] is True
    assert post_data["publish_decision_path"] == "human_approved"


def test_invalid_model_output_is_classified_and_blocked(monkeypatch, authed_client):
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
    task_id = response.json()["data"]["id"]
    assert response.json()["data"]["status"] == "failed"

    detail = authed_client.get(f"/api/tasks/{task_id}")
    assert detail.status_code == 200
    data = detail.json()["data"]
    assert data["status"] == "failed"
    assert data["error_code"] == "invalid_model_output"
    assert data["post_id"] is None
    assert any(
        item["stage"] == "qa_completed" and item["detail"].get("integrity_ok") is False
        for item in data["trace"]["trace_events"]
    )


@pytest.mark.parametrize(
    ("error_factory", "expected_code"),
    [
        (lambda: httpx.ConnectTimeout("connect timeout"), "llm_connect_timeout"),
        (lambda: httpx.ReadTimeout("read timeout"), "llm_read_timeout"),
        (
            lambda: httpx.HTTPStatusError(
                "auth failed",
                request=httpx.Request("POST", "https://api.example.com/v1/chat/completions"),
                response=httpx.Response(401),
            ),
            "llm_auth_error",
        ),
        (
            lambda: httpx.HTTPStatusError(
                "upstream failed",
                request=httpx.Request("POST", "https://api.example.com/v1/chat/completions"),
                response=httpx.Response(503),
            ),
            "llm_upstream_5xx",
        ),
    ],
)
def test_llm_errors_are_classified(monkeypatch, authed_client, error_factory, expected_code):
    async def broken_chat(self, **_kwargs):  # noqa: ANN001
        raise error_factory()

    monkeypatch.setattr(LLMAdapter, "chat", broken_chat)

    response = authed_client.post(
        "/api/tasks/trigger",
        json={"trigger_source": "manual", "semantic_hint": "classify llm failure", "payload": {"kind": "manual"}},
    )
    assert response.status_code == 200
    task_id = response.json()["data"]["id"]
    assert response.json()["data"]["status"] == "failed"

    detail = authed_client.get(f"/api/tasks/{task_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["error_code"] == expected_code


def test_scheduled_generation_uses_scheduler_event_type(authed_client):
    asyncio.run(scheduled_generation_job())

    tasks = authed_client.get("/api/tasks")
    assert tasks.status_code == 200
    latest_task = tasks.json()["data"]["items"][0]
    assert latest_task["trigger_source"] == "scheduler"

    events = authed_client.get("/api/events")
    assert events.status_code == 200
    latest_event = events.json()["data"]["items"][0]
    assert latest_event["event_type"] == "scheduler"
    assert latest_event["source"] == "scheduler"


def test_failed_webhook_auth_does_not_poison_dedup_or_cooldown(authed_client):
    update = authed_client.put(
        "/api/config",
        json={
            "items": [
                {"key": "webhook.auth_mode", "value": "bearer", "category": "webhook"},
                {"key": "webhook.auth_token", "value": "top-secret-token", "category": "webhook"},
            ]
        },
    )
    assert update.status_code == 200

    payload = {"source": "integration-test", "kind": "webhook"}
    failed = authed_client.post(
        "/api/webhook/trigger",
        json=payload,
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert failed.status_code == 401

    succeeded = authed_client.post(
        "/api/webhook/trigger",
        json=payload,
        headers={"Authorization": "Bearer top-secret-token"},
    )
    assert succeeded.status_code == 200
    assert succeeded.json()["data"]["task_status"] == "published"
