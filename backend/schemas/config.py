from __future__ import annotations

import json
import re
from urllib.parse import urlparse

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

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str | None, info) -> str | None:
        key = info.data.get("key")
        if key is None or value is None:
            return value
        if key.endswith(".api_key") and value == "******":
            return value
        _validate_config_value(key, value)
        return value


class ConfigUpdateRequest(BaseModel):
    items: list[ConfigEntry]


class RevealSecretRequest(BaseModel):
    key: str


class TestProviderRequest(BaseModel):
    base_url: str
    api_key: str
    model_id: str


def _validate_config_value(key: str, value: str) -> None:
    stripped = value.strip()
    if key in {"llm.base_url", "embedding.base_url", "notify.webhook_url"}:
        _validate_optional_url(key, stripped)
    elif key == "hugo.base_url":
        if stripped != "/":
            _validate_optional_url(key, stripped)
    elif key == "site.domain":
        _validate_optional_domain(key, stripped)
    elif key == "panel.port":
        _validate_int_range(key, stripped, min_value=1024, max_value=65535)
    elif key in {
        "schedule.days_per_cycle",
        "schedule.posts_per_cycle",
        "schedule.sample_interval_minutes",
        "qa.max_retries",
        "qa.min_length",
        "qa.max_length",
        "webhook.cooldown_seconds",
        "anti_perfection.consecutive_max",
        "anti_perfection.cooldown_hours",
        "sensory.blind_zone_minutes",
    }:
        _validate_int_range(key, stripped, min_value=0)
    elif key in {
        "budget.daily_limit_usd",
        "budget.monthly_limit_usd",
        "qa.duplicate_threshold",
        "sensory.cpu_high_threshold",
        "sensory.mem_high_threshold",
        "sensory.io_high_threshold",
    }:
        _validate_float_range(key, stripped, min_value=0.0)
    elif key in {"budget.is_hibernating", "notify.enabled", "anti_perfection.enabled"}:
        if stripped not in {"0", "1", "true", "false", "yes", "no", "on", "off"}:
            raise ValueError(f"{key} must be a boolean-like value")
    elif key == "schedule.publish_time":
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", stripped):
            raise ValueError("schedule.publish_time must use HH:MM in 24-hour time")
    elif key in {"schedule.review_cron", "schedule.decay_cron"}:
        _validate_cron(key, stripped)
    elif key in {"qa.forbidden_words", "qa.template_phrases"}:
        _validate_json_string_array(key, stripped)
    elif key == "qa.required_language":
        if stripped not in {"zh", "en", "any"}:
            raise ValueError("qa.required_language must be one of zh, en, any")
    elif key == "webhook.auth_mode":
        if stripped not in {"bearer", "hmac"}:
            raise ValueError("webhook.auth_mode must be bearer or hmac")
    elif key == "sensory.source_mode":
        if stripped not in {"container", "host"}:
            raise ValueError("sensory.source_mode must be container or host")

    if key == "qa.max_length":
        _validate_int_range(key, stripped, min_value=1)
    bounded_percent_keys = {
        "qa.duplicate_threshold",
        "sensory.cpu_high_threshold",
        "sensory.mem_high_threshold",
        "sensory.io_high_threshold",
    }
    if key in bounded_percent_keys:
        max_value = 1.0 if key == "qa.duplicate_threshold" else 100.0
        _validate_float_range(key, stripped, min_value=0.0, max_value=max_value)


def _validate_optional_url(key: str, value: str) -> None:
    if not value:
        return
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{key} must be an http(s) URL")


def _validate_optional_domain(key: str, value: str) -> None:
    if not value:
        return
    if "://" in value or "/" in value or "@" in value:
        raise ValueError(f"{key} must be a bare domain without scheme or path")
    if len(value) > 253 or not re.fullmatch(r"(?=.{1,253}$)(?!-)[A-Za-z0-9.-]+(?<!-)", value):
        raise ValueError(f"{key} must be a valid domain")
    if any(not part or part.startswith("-") or part.endswith("-") or len(part) > 63 for part in value.split(".")):
        raise ValueError(f"{key} must be a valid domain")


def _validate_int_range(key: str, value: str, *, min_value: int | None = None, max_value: int | None = None) -> None:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer") from exc
    if min_value is not None and parsed < min_value:
        raise ValueError(f"{key} must be >= {min_value}")
    if max_value is not None and parsed > max_value:
        raise ValueError(f"{key} must be <= {max_value}")


def _validate_float_range(
    key: str,
    value: str,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
) -> None:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{key} must be a number") from exc
    if min_value is not None and parsed < min_value:
        raise ValueError(f"{key} must be >= {min_value}")
    if max_value is not None and parsed > max_value:
        raise ValueError(f"{key} must be <= {max_value}")


def _validate_cron(key: str, value: str) -> None:
    if not value:
        raise ValueError(f"{key} cannot be empty")
    parts = value.split()
    if len(parts) != 5:
        raise ValueError(f"{key} must contain 5 cron fields")
    if not all(re.fullmatch(r"[\d*/,\-]+", part) for part in parts):
        raise ValueError(f"{key} contains unsupported cron syntax")


def _validate_json_string_array(key: str, value: str) -> None:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError as exc:
        raise ValueError(f"{key} must be a JSON array") from exc
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise ValueError(f"{key} must be a JSON array of strings")
