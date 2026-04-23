from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import SystemConfig
from backend.security.encryption import ConfigEncryptor
from backend.utils.serde import json_loads

SECRET_KEYS = {
    "llm.api_key",
    "embedding.api_key",
    "webhook.auth_token",
    "notify.bearer_token",
}
HIDDEN_KEYS = {
    "system.encryption_key",
}
DEPRECATED_CONFIG_KEYS = {
    "schedule.posts_per_day",
    "schedule.cron_expression",
    "system.version",
}
CATEGORY_BY_PREFIX = {
    "site": "site",
    "panel": "panel",
    "llm": "llm",
    "embedding": "embedding",
    "schedule": "schedule",
    "budget": "budget",
    "qa": "qa",
    "webhook": "webhook",
    "notify": "notify",
    "anti_perfection": "anti_perfection",
    "sensory": "sensory",
    "hugo": "hugo",
    "system": "system",
}


def infer_category(key: str, fallback: str = "general") -> str:
    prefix = key.split(".", 1)[0]
    return CATEGORY_BY_PREFIX.get(prefix, fallback)


class ConfigStore:
    def __init__(self, db: AsyncSession, encryptor: ConfigEncryptor | None = None):
        self.db = db
        self.encryptor = encryptor

    async def all(self) -> list[SystemConfig]:
        result = await self.db.scalars(select(SystemConfig).order_by(SystemConfig.category, SystemConfig.key))
        return list(result)

    async def by_category(self, category: str) -> list[SystemConfig]:
        result = await self.db.scalars(
            select(SystemConfig).where(SystemConfig.category == category).order_by(SystemConfig.key)
        )
        return list(result)

    async def get(self, key: str, default: str | None = None, decrypt: bool = True) -> str | None:
        entry = await self.db.get(SystemConfig, key)
        if entry is None:
            return default
        value = entry.value
        if decrypt and entry.encrypted and value and self.encryptor:
            return self.encryptor.decrypt(value)
        return value if value is not None else default

    async def set(
        self,
        key: str,
        value: str | None,
        *,
        category: str | None = None,
        encrypted: bool | None = None,
    ) -> SystemConfig:
        entry = await self.db.get(SystemConfig, key)
        if entry is None:
            entry = SystemConfig(
                key=key,
                value="",
                category=infer_category(key, category or "general"),
                encrypted=0,
                updated_at="",
            )
            self.db.add(entry)
            await self.db.flush()
        entry.category = infer_category(key, category or entry.category or "general")
        should_encrypt = key in SECRET_KEYS or bool(encrypted)
        entry.encrypted = 1 if should_encrypt else 0
        if value is None:
            entry.value = None
        elif should_encrypt and self.encryptor:
            entry.value = self.encryptor.encrypt(value)
        else:
            entry.value = value
        await self.db.flush()
        return entry

    async def bulk_update(self, items: Iterable[dict]) -> None:
        for item in items:
            if item["key"] in SECRET_KEYS and item.get("value") == "******":
                continue
            await self.set(
                item["key"],
                item.get("value"),
                category=item.get("category"),
                encrypted=item.get("encrypted"),
            )

    async def as_public_dict(self, category: str | None = None) -> dict[str, dict]:
        entries = await (self.by_category(category) if category else self.all())
        data: dict[str, dict] = {}
        for entry in entries:
            if entry.key in HIDDEN_KEYS:
                continue
            value = entry.value
            if entry.key in SECRET_KEYS and value:
                if entry.encrypted and self.encryptor:
                    decrypted = self.encryptor.decrypt(value)
                    value = "******" if decrypted else ""
                else:
                    value = "******"
            data[entry.key] = {
                "value": value,
                "category": entry.category,
                "encrypted": bool(entry.encrypted),
            }
        return data

    async def purge_deprecated_keys(self) -> list[str]:
        rows = await self.db.scalars(select(SystemConfig).where(SystemConfig.key.in_(tuple(DEPRECATED_CONFIG_KEYS))))
        stale = list(rows)
        for row in stale:
            await self.db.delete(row)
        if stale:
            await self.db.flush()
        return sorted(item.key for item in stale)

    async def get_json(self, key: str, default: list | dict) -> list | dict:
        return json_loads(await self.get(key, "", decrypt=False), default)
