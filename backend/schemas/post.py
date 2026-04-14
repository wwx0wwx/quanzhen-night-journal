from __future__ import annotations

from pydantic import BaseModel, Field

from backend.schemas.common import ORMModel


class PostBase(BaseModel):
    title: str
    slug: str | None = None
    front_matter: dict = Field(default_factory=dict)
    content_markdown: str = ""
    summary: str = ""
    status: str = "draft"
    persona_id: int | None = None
    publish_target: str = "hugo"
    review_info: dict = Field(default_factory=dict)


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    front_matter: dict | None = None
    content_markdown: str | None = None
    summary: str | None = None
    status: str | None = None
    review_info: dict | None = None


class PostOut(ORMModel, PostBase):
    id: int
    task_id: int | None = None
    published_at: str | None = None
    revision: int
    digital_stamp: str | None = None
    created_at: str
    updated_at: str


class RevisionOut(ORMModel):
    id: int
    post_id: int
    revision: int
    title: str
    content_markdown: str
    front_matter: str
    change_reason: str
    created_at: str
