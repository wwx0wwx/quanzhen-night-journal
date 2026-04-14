def test_memory_create_and_search(authed_client):
    created = authed_client.post(
        "/api/memories",
        json={
            "persona_id": 1,
            "level": "L0",
            "content": "机箱风声贴着木纹走过去，像潮水很慢地退。",
            "summary": "机箱风声像潮水退去。",
            "tags": ["core"],
            "source": "hand_written",
            "weight": 1.0,
            "review_status": "reviewed",
            "decay_strategy": "standard",
            "is_core": True,
        },
    )
    assert created.status_code == 200

    searched = authed_client.post(
        "/api/memories/search",
        json={"query": "风声和机箱", "persona_id": 1, "top_k": 5},
    )
    assert searched.status_code == 200
    assert searched.json()["data"]
