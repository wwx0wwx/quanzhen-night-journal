import asyncio

from backend.engine.generation_orchestrator import GenerationOrchestrator
from backend.engine.prompt_builder import PromptBuilder
from backend.models import Persona
from backend.utils.serde import json_dumps
from backend.utils.time import utcnow_iso


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


def test_prompt_builder_includes_persona_taboos():
    persona = Persona(
        id=1,
        name="测试人格",
        description="",
        is_active=1,
        is_default=1,
        identity_setting="负责夜记",
        worldview_setting="庭院与长夜",
        language_style="短句",
        taboos=json_dumps(["不要使用现代网络流行语", "不要复写上一场雨夜"]),
        sensory_lexicon="{}",
        structure_preference="medium",
        expression_intensity="moderate",
        stability_params=json_dumps({"temperature_base": 0.7, "temperature_range": [0.3, 1.0]}),
        scene_pool="[]",
        created_at=utcnow_iso(),
        updated_at=utcnow_iso(),
    )

    block = PromptBuilder()._build_persona_block(persona)

    assert "硬性禁忌" in block
    assert "- 不要使用现代网络流行语" in block
    assert "- 不要复写上一场雨夜" in block
    assert "以禁忌为准" in block


def test_generation_uses_persona_stability_temperature():
    class FakeConfigStore:
        async def get(self, key, default="", **kwargs):  # noqa: ANN001, ANN003
            values = {
                "llm.base_url": "",
                "llm.api_key": "",
                "llm.model_id": "",
                "llm.max_tokens": "1200",
            }
            return values.get(key, default)

    class FakeLLMAdapter:
        def __init__(self):
            self.calls = []

        async def chat(self, **kwargs):  # noqa: ANN003
            self.calls.append(kwargs)
            return "# 题\n\n正文。", {"prompt_tokens": 1, "completion_tokens": 1}, 3

    async def exercise() -> None:
        persona = Persona(
            id=1,
            name="测试人格",
            description="",
            is_active=1,
            is_default=1,
            identity_setting="",
            worldview_setting="",
            language_style="",
            taboos="[]",
            sensory_lexicon="{}",
            structure_preference="medium",
            expression_intensity="moderate",
            stability_params=json_dumps({"temperature_base": 0.55, "temperature_range": [0.2, 0.88]}),
            scene_pool="[]",
            created_at=utcnow_iso(),
            updated_at=utcnow_iso(),
        )
        llm = FakeLLMAdapter()
        orchestrator = GenerationOrchestrator.__new__(GenerationOrchestrator)
        orchestrator.config_store = FakeConfigStore()
        orchestrator.llm_adapter = llm

        await orchestrator._generate("prompt", persona, anti_perfection=False)
        await orchestrator._generate("prompt", persona, anti_perfection=True)

        assert llm.calls[0]["temperature"] == 0.55
        assert llm.calls[0]["max_tokens"] == 1200
        assert llm.calls[1]["temperature"] == 0.88
        assert llm.calls[1]["max_tokens"] == 2400

    asyncio.run(exercise())
