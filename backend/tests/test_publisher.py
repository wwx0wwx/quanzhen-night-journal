import json
from pathlib import Path

from backend.config import get_settings


def test_publish_writes_markdown_file(authed_client):
    created = authed_client.post(
        "/api/posts",
        json={
            "title": "手动夜记",
            "slug": "manual-night-note",
            "front_matter": {"title": "手动夜记"},
            "content_markdown": "这里是一篇手动写入的测试文章。",
            "summary": "测试文章",
            "status": "approved",
            "persona_id": 1,
            "publish_target": "hugo",
            "review_info": {},
        },
    )
    post_id = created.json()["data"]["id"]
    published = authed_client.post(f"/api/posts/{post_id}/publish")
    assert published.status_code == 200

    assert published.json()["data"]["status"] == "published"
    settings = get_settings()
    file_path = Path(settings.hugo_post_path / "manual-night-note.md")
    assert file_path.exists()


def test_publish_uses_clean_front_matter_and_strips_duplicate_h1(authed_client):
    created = authed_client.post(
        "/api/posts",
        json={
            "title": "全真夜记：雨点与屏息",
            "slug": "rain-note",
            "front_matter": {"title": "旧标题", "summary": "旧摘要"},
            "content_markdown": "# 全真夜记：雨点与屏息\n\n窗外的风沿着机房的壳体慢慢滑过去。",
            "summary": "窗外的风沿着机房的壳体慢慢滑过去。",
            "status": "approved",
            "persona_id": 1,
            "publish_target": "hugo",
            "review_info": {},
        },
    )
    assert created.status_code == 200

    post_id = created.json()["data"]["id"]
    published = authed_client.post(f"/api/posts/{post_id}/publish")
    assert published.status_code == 200

    settings = get_settings()
    file_path = Path(settings.hugo_post_path / "rain-note.md")
    body = file_path.read_text(encoding="utf-8")
    assert 'title: "全真夜记：雨点与屏息"' in body
    assert 'summary: "窗外的风沿着机房的壳体慢慢滑过去。"' in body
    assert 'description: "窗外的风沿着机房的壳体慢慢滑过去。"' in body
    assert body.count("# 全真夜记：雨点与屏息") == 0
