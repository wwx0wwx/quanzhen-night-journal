from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import SystemConfig
from backend.utils.time import utcnow_iso


class ConfigEncryptor:
    def __init__(self, key: bytes):
        self.fernet = Fernet(key)

    @classmethod
    def generate_key(cls) -> bytes:
        return Fernet.generate_key()

    def encrypt(self, value: str) -> str:
        return self.fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, token: str) -> str:
        try:
            return self.fernet.decrypt(token.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("invalid_encrypted_value") from exc


async def ensure_encryptor(db: AsyncSession) -> tuple[ConfigEncryptor, bool]:
    entry = await db.get(SystemConfig, "system.encryption_key")
    created = entry is None or not entry.value
    if created:
        key = ConfigEncryptor.generate_key().decode("utf-8")
        if entry is None:
            entry = SystemConfig(
                key="system.encryption_key",
                value=key,
                encrypted=0,
                category="system",
                updated_at=utcnow_iso(),
            )
            db.add(entry)
        else:
            entry.value = key
            entry.updated_at = utcnow_iso()
        await db.flush()
        return ConfigEncryptor(key.encode("utf-8")), True
    return ConfigEncryptor(entry.value.encode("utf-8")), False
