from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from backend.schemas.common import ORMModel
from backend.utils.text_integrity import ensure_text_integrity


class PersonaBase(BaseModel):
    name: str
    description: str = ""
    is_active: bool = True
    identity_setting: str = ""
    worldview_setting: str = ""
    language_style: str = ""
    taboos: list[str] = Field(default_factory=list)
    sensory_lexicon: dict[str, str] = Field(default_factory=dict)
    structure_preference: str = "medium"
    expression_intensity: str = "moderate"
    stability_params: dict = Field(
        default_factory=lambda: {"temperature_base": 0.7, "temperature_range": [0.3, 1.2]}
    )
    scene_pool: list[dict[str, str]] = Field(default_factory=list)

    @field_validator("name", "description", "identity_setting", "worldview_setting", "language_style")
    @classmethod
    def validate_text_integrity(cls, value: str, info) -> str:  # noqa: ANN001
        return ensure_text_integrity(value, info.field_name)

    @field_validator("sensory_lexicon")
    @classmethod
    def validate_lexicon_integrity(cls, value: dict[str, str]) -> dict[str, str]:
        for key, item in value.items():
            ensure_text_integrity(key, "sensory_lexicon.key")
            ensure_text_integrity(item, "sensory_lexicon.value")
        return value

    @field_validator("scene_pool")
    @classmethod
    def validate_scene_pool_integrity(cls, value: list[dict[str, str]]) -> list[dict[str, str]]:
        for scene in value:
            for key, item in scene.items():
                ensure_text_integrity(item, f"scene_pool.{key}")
        return value


class PersonaCreate(PersonaBase):
    is_default: bool = False


class PersonaUpdate(PersonaBase):
    is_default: bool | None = None


class PersonaOut(ORMModel, PersonaBase):
    id: int
    is_default: bool
    created_at: str
    updated_at: str
