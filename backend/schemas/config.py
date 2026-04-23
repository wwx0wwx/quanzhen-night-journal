from __future__ import annotations

from pydantic import BaseModel, field_validator

ALLOWED_CONFIG_PREFIXES = frozenset(
    {
        "anti_perfection.",
        "budget.",
        "embedding.",
        "hugo.",
        "llm.",
        "notify.",
        "panel.",
        "qa.",
        "schedule.",
        "sensory.",
        "site.",
        "system.",
        "webhook.",
    }
)


class ConfigEntry(BaseModel):
    key: str
    value: str | None = None
    encrypted: bool = False
    category: str = "general"

    @field_validator("key")
    @classmethod
    def validate_key_prefix(cls, v: str) -> str:
        if not any(v.startswith(prefix) for prefix in ALLOWED_CONFIG_PREFIXES):
            raise ValueError(f"config key '{v}' does not match any allowed prefix")
        return v


class ConfigUpdateRequest(BaseModel):
    items: list[ConfigEntry]


class TestProviderRequest(BaseModel):
    base_url: str
    api_key: str
    model_id: str
