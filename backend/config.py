from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_JWT_SECRET = "quanzhen-dev-secret-please-change-before-production-2026"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "全真夜记 Core"
    app_version: str = "1.0.7"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    jwt_secret: str = Field(
        default=DEFAULT_JWT_SECRET,
        alias="JWT_SECRET",
    )
    jwt_expire_hours: int = Field(default=24, alias="JWT_EXPIRE_HOURS")
    cookie_name: str = Field(default="qz_token", alias="COOKIE_NAME")
    database_url: str = Field(
        default=f"sqlite+aiosqlite:///{(ROOT_DIR / 'data' / 'quanzhen.db').as_posix()}",
        alias="DATABASE_URL",
    )
    site_base_url: str = Field(default="http://localhost:5210", alias="SITE_BASE_URL")
    build_signal_file: str = Field(
        default=str(ROOT_DIR / "data" / ".build_signal"),
        alias="BUILD_SIGNAL_FILE",
    )
    build_status_file: str = Field(
        default=str(ROOT_DIR / "data" / "build_status.json"),
        alias="BUILD_STATUS_FILE",
    )
    hugo_content_dir: str = Field(
        default=str(ROOT_DIR / "content"),
        alias="HUGO_CONTENT_DIR",
    )
    hugo_public_dir: str = Field(
        default=str(ROOT_DIR / "public"),
        alias="HUGO_PUBLIC_DIR",
    )
    seed_content_dir: str = Field(
        default=str(ROOT_DIR / "content"),
        alias="SEED_CONTENT_DIR",
    )
    seed_draft_dir: str = Field(
        default=str(ROOT_DIR / "draft_review"),
        alias="SEED_DRAFT_DIR",
    )
    automation_dir: str = Field(
        default=str(ROOT_DIR / "automation"),
        alias="AUTOMATION_DIR",
    )
    import_legacy_assets: bool = Field(default=False, alias="IMPORT_LEGACY_ASSETS")
    ghost_dir: str = Field(
        default=str(ROOT_DIR / "data" / "ghosts"),
        alias="GHOST_DIR",
    )
    allow_fake_llm: bool = Field(default=False, alias="ALLOW_FAKE_LLM")
    llm_request_timeout_seconds: float = Field(default=60.0, alias="LLM_REQUEST_TIMEOUT_SECONDS")
    llm_request_retries: int = Field(default=2, alias="LLM_REQUEST_RETRIES")
    llm_retry_backoff_seconds: float = Field(default=1.0, alias="LLM_RETRY_BACKOFF_SECONDS")
    public_server_ip: str = Field(default="", alias="PUBLIC_SERVER_IP")
    acme_email: str = Field(default="", alias="ACME_EMAIL")
    caddy_reload_url: str = Field(
        default="http://caddy:2019/load",
        alias="CADDY_RELOAD_URL",
    )
    caddy_reload_enabled: bool = Field(default=False, alias="CADDY_RELOAD_ENABLED")
    allow_cloudflare_proxy_domain: bool = Field(default=False, alias="ALLOW_CLOUDFLARE_PROXY_DOMAIN")
    cors_origins: str = Field(default="", alias="CORS_ORIGINS")
    default_preset: str = Field(default="quanzhen", alias="DEFAULT_PRESET")
    presets_dir: str = Field(
        default=str(ROOT_DIR / "presets"),
        alias="PRESETS_DIR",
    )

    @property
    def root_dir(self) -> Path:
        return ROOT_DIR

    @property
    def data_dir(self) -> Path:
        return self.root_dir / "data"

    @property
    def database_path(self) -> Path:
        prefix = "sqlite+aiosqlite:///"
        if self.database_url.startswith(prefix):
            return Path(self.database_url[len(prefix) :])
        return self.data_dir / "quanzhen.db"

    @property
    def schema_path(self) -> Path:
        return self.root_dir / "doc" / "database_schema.sql"

    @property
    def hugo_content_path(self) -> Path:
        return Path(self.hugo_content_dir)

    @property
    def hugo_post_path(self) -> Path:
        return self.hugo_content_path / "posts"

    @property
    def hugo_public_path(self) -> Path:
        return Path(self.hugo_public_dir)

    @property
    def build_signal_path(self) -> Path:
        return Path(self.build_signal_file)

    @property
    def build_status_path(self) -> Path:
        return Path(self.build_status_file)

    @property
    def seed_content_path(self) -> Path:
        return Path(self.seed_content_dir)

    @property
    def seed_draft_path(self) -> Path:
        return Path(self.seed_draft_dir)

    @property
    def automation_path(self) -> Path:
        return Path(self.automation_dir)

    @property
    def ghost_path(self) -> Path:
        return Path(self.ghost_dir)

    @property
    def presets_path(self) -> Path:
        return Path(self.presets_dir)

    @property
    def runtime_caddyfile_path(self) -> Path:
        return self.data_dir / "Caddyfile"

    @property
    def runtime_hugo_config_path(self) -> Path:
        return self.data_dir / "hugo.toml"

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() in {"prod", "production"}

    def validate_runtime(self) -> None:
        if self.is_production and self.jwt_secret.strip() == DEFAULT_JWT_SECRET:
            raise RuntimeError("production environment requires a custom JWT_SECRET")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    if os.getenv("PYTEST_CURRENT_TEST"):
        return Settings(_env_file=None)
    return Settings()
