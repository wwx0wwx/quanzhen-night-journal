from __future__ import annotations

from pydantic import BaseModel


class ConfigEntry(BaseModel):
    key: str
    value: str | None = None
    encrypted: bool = False
    category: str = "general"


class ConfigUpdateRequest(BaseModel):
    items: list[ConfigEntry]


class TestProviderRequest(BaseModel):
    base_url: str
    api_key: str
    model_id: str
