def test_persona_crud(authed_client):
    created = authed_client.post(
        "/api/personas",
        json={
            "name": "侧人格",
            "description": "偏向冷静记录的测试人格",
            "is_active": True,
            "is_default": False,
            "identity_setting": "负责观察",
            "worldview_setting": "一切都会留下回音",
            "language_style": "短句",
            "taboos": ["夸张"],
            "sensory_lexicon": {"normal": "一切平稳"},
            "structure_preference": "medium",
            "expression_intensity": "moderate",
            "stability_params": {"temperature_base": 0.7, "temperature_range": [0.3, 1.0]},
        },
    )
    assert created.status_code == 200
    persona_id = created.json()["data"]["id"]

    activated = authed_client.post(f"/api/personas/{persona_id}/activate")
    assert activated.status_code == 200
    assert activated.json()["data"]["is_default"] is True

    listing = authed_client.get("/api/personas")
    assert len(listing.json()["data"]) >= 2
