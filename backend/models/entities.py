from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_initialized: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)


class SystemConfig(Base):
    __tablename__ = "system_config"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    encrypted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    category: Mapped[str] = mapped_column(Text, nullable=False, default="general")
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)


class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_default: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    identity_setting: Mapped[str] = mapped_column(Text, nullable=False, default="")
    worldview_setting: Mapped[str] = mapped_column(Text, nullable=False, default="")
    language_style: Mapped[str] = mapped_column(Text, nullable=False, default="")
    taboos: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    sensory_lexicon: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    structure_preference: Mapped[str] = mapped_column(Text, nullable=False, default="medium")
    expression_intensity: Mapped[str] = mapped_column(Text, nullable=False, default="moderate")
    stability_params: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id", ondelete="CASCADE"))
    level: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    source: Mapped[str] = mapped_column(Text, nullable=False, default="auto_summary")
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    time_range_start: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_range_end: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(Text, nullable=False, default="unreviewed")
    decay_strategy: Mapped[str] = mapped_column(Text, nullable=False, default="standard")
    is_core: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    last_accessed_at: Mapped[str | None] = mapped_column(Text, nullable=True)


class MemoryVector(Base):
    __tablename__ = "memory_vectors"

    memory_id: Mapped[int] = mapped_column(
        ForeignKey("memories.id", ondelete="CASCADE"),
        primary_key=True,
    )
    embedding: Mapped[str] = mapped_column(Text, nullable=False, default="[]")


class SensorySnapshot(Base):
    __tablename__ = "sensory_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(Text, nullable=False, default="container")
    sampled_at: Mapped[str] = mapped_column(Text, nullable=False)
    cpu_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    io_read_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    io_write_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    disk_usage_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    network_rx_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    network_tx_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    load_average: Mapped[float | None] = mapped_column(Float, nullable=True)
    api_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tags: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    translated_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    persona_id: Mapped[int | None] = mapped_column(
        ForeignKey("personas.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_in_blind_zone: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False, default="")
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    normalized_semantic: Mapped[str] = mapped_column(Text, nullable=False, default="")
    auth_status: Mapped[str] = mapped_column(Text, nullable=False, default="not_required")
    dedup_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    cooldown_status: Mapped[str] = mapped_column(Text, nullable=False, default="ready")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("generation_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )


class PublicPageView(Base):
    __tablename__ = "public_page_views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path: Mapped[str] = mapped_column(Text, nullable=False, default="/")
    page_title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    referrer: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ip_address: Mapped[str] = mapped_column(Text, nullable=False, default="")
    user_agent: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)


class GenerationTask(Base):
    __tablename__ = "generation_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trigger_source: Mapped[str] = mapped_column(Text, nullable=False)
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"),
        nullable=True,
    )
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id", ondelete="RESTRICT"))
    context_snapshot: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    memory_hits: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    sensory_snapshot_id: Mapped[int | None] = mapped_column(
        ForeignKey("sensory_snapshots.id", ondelete="SET NULL"),
        nullable=True,
    )
    prompt_summary: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    generated_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    qa_result: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    token_input: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    token_output: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_estimate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="queued")
    cold_start: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    anti_perfection: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    queue_wait_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trace_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[str] = mapped_column(Text, nullable=False)
    finished_at: Mapped[str | None] = mapped_column(Text, nullable=True)
    post_id: Mapped[int | None] = mapped_column(
        ForeignKey("posts.id", ondelete="SET NULL"),
        nullable=True,
    )


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    slug: Mapped[str] = mapped_column(Text, nullable=False, default="")
    front_matter: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False, default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")
    persona_id: Mapped[int | None] = mapped_column(
        ForeignKey("personas.id", ondelete="SET NULL"),
        nullable=True,
    )
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("generation_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    published_at: Mapped[str | None] = mapped_column(Text, nullable=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    publish_target: Mapped[str] = mapped_column(Text, nullable=False, default="hugo")
    digital_stamp: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_info: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)


class PostVector(Base):
    __tablename__ = "post_vectors"

    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    embedding: Mapped[str] = mapped_column(Text, nullable=False, default="[]")


class PostRevision(Base):
    __tablename__ = "post_revisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    front_matter: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    change_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str] = mapped_column(Text, nullable=False, default="system")
    action: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    ip_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(Text, nullable=False, default="info")


class AuditEventDefinition(Base):
    __tablename__ = "audit_event_definitions"

    action: Mapped[str] = mapped_column(Text, primary_key=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    target_label: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)


class CostRecord(Base):
    __tablename__ = "cost_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("generation_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    call_type: Mapped[str] = mapped_column(Text, nullable=False)
    model_id: Mapped[str] = mapped_column(Text, nullable=False, default="")
    token_input: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    token_output: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    token_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_estimate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(Text, nullable=False, default="USD")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    response_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class FolderMonitor(Base):
    __tablename__ = "folder_monitors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    file_types: Mapped[str] = mapped_column(Text, nullable=False, default='["txt", "md"]')
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
