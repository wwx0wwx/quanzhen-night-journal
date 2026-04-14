from __future__ import annotations

from backend.adapters.llm_adapter import LLMAdapter
from backend.utils.post_content import derive_summary, extract_title
from backend.utils.slug import is_placeholder_slug, slugify


def test_slugify_supports_chinese_english_mixed_and_fallback():
    assert slugify("全真夜记：雨点与屏息") == "全真夜记-雨点与屏息"
    assert slugify("Night Journal at Dawn") == "night-journal-at-dawn"
    assert slugify("全真 Night Note 2026") == "全真-night-note-2026"

    fallback = slugify("  !!!  ", fallback_prefix="post")
    assert fallback.startswith("post-")
    assert fallback != "untitled"
    assert is_placeholder_slug("2-untitled")
    assert is_placeholder_slug("untitled")
    assert not is_placeholder_slug("全真夜记-雨点与屏息")


def test_extract_title_prefers_markdown_heading_and_cleans_noise():
    content = "\n\n   # 全真夜记：雨点与屏息  \n\n窗户在回声里轻轻震动。"
    assert extract_title(content) == "全真夜记：雨点与屏息"


def test_extract_title_falls_back_to_first_sentence_and_summary_skips_heading():
    content = "\n\n***\n雨点落在窗沿。夜还没有结束。"
    assert extract_title(content) == "雨点落在窗沿"
    assert derive_summary("# 全真夜记：雨点与屏息\n\n窗户在回声里轻轻震动。", title="全真夜记：雨点与屏息") == "窗户在回声里轻轻震动。"


def test_generation_uses_clean_title_and_unicode_slug(monkeypatch, authed_client):
    async def titled_chat(self, **_kwargs):  # noqa: ANN001
        content = "# 全真夜记：雨点与屏息\n\n窗外的风沿着机房的壳体慢慢滑过去。"
        usage = {"prompt_tokens": 12, "completion_tokens": 30}
        return content, usage, 5

    monkeypatch.setattr(LLMAdapter, "chat", titled_chat)

    config = authed_client.put(
        "/api/config",
        json={"items": [{"key": "qa.min_length", "value": "1", "category": "qa"}]},
    )
    assert config.status_code == 200

    response = authed_client.post(
        "/api/tasks/trigger",
        json={"trigger_source": "manual", "semantic_hint": "write a Chinese note", "payload": {"kind": "manual"}},
    )
    assert response.status_code == 200
    task = response.json()["data"]
    assert task["status"] == "published"

    posts = authed_client.get("/api/posts")
    assert posts.status_code == 200
    latest = posts.json()["data"]["items"][0]
    assert latest["title"] == "全真夜记：雨点与屏息"
    assert latest["slug"] == f"{task['id']}-全真夜记-雨点与屏息"
    assert latest["summary"].startswith("窗外的风沿着机房的壳体慢慢滑过去")


def test_manual_post_create_derives_clean_title_and_unique_slug(authed_client):
    first = authed_client.post(
        "/api/posts",
        json={"title": "  # 全真夜记：雨点与屏息 ", "content_markdown": "窗外的风沿着机房的壳体慢慢滑过去。"},
    )
    assert first.status_code == 200
    assert first.json()["data"]["title"] == "全真夜记：雨点与屏息"
    assert first.json()["data"]["slug"] == "全真夜记-雨点与屏息"

    second = authed_client.post(
        "/api/posts",
        json={"title": "# 全真夜记：雨点与屏息", "content_markdown": "另一篇内容。"},
    )
    assert second.status_code == 200
    assert second.json()["data"]["slug"] == "全真夜记-雨点与屏息-2"


def test_manual_post_create_and_update_regenerate_title_and_slug_from_content(authed_client):
    create = authed_client.post(
        "/api/posts",
        json={"title": "   ", "content_markdown": "# 风吹过机房\n\n冷风贴着灯带走了一圈。"},
    )
    assert create.status_code == 200
    created = create.json()["data"]
    assert created["title"] == "风吹过机房"
    assert created["slug"] == "风吹过机房"

    update = authed_client.put(
        f"/api/posts/{created['id']}",
        json={"title": " # 新的标题 ", "slug": "", "summary": "", "content_markdown": "# 新的标题\n\n内容更新。"},
    )
    assert update.status_code == 200
    updated = update.json()["data"]
    assert updated["title"] == "新的标题"
    assert updated["slug"] == "新的标题"
    assert updated["summary"] == "内容更新。"


def test_manual_post_ignores_placeholder_slug_and_uses_title(authed_client):
    response = authed_client.post(
        "/api/posts",
        json={"title": "# 雨还在门口", "slug": "2-untitled", "content_markdown": "门口还有潮湿的风。"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["slug"] == "雨还在门口"
