from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)


class SetupCompleteRequest(BaseModel):
    new_password: str = Field(min_length=8)
    site_title: str = ""
    site_subtitle: str = ""
    site_domain: str = ""
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model_id: str = ""
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model_id: str = ""
