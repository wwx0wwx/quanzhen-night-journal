from __future__ import annotations

import logging
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.models import SystemConfig
from backend.utils.time import utcnow_iso

logger = logging.getLogger(__name__)

# Legacy DB key name — still read for migration, no longer written for new installs.
LEGACY_DB_KEY = "system.encryption_key"


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


def _normalize_key(raw: str) -> str:
    return raw.strip().strip('"').strip("'")


def _key_file_path() -> Path:
    """Keep key next to the DB file so test/tmp deployments stay isolated."""
    settings = get_settings()
    return settings.database_path.parent / ".encryption_key"


def _read_key_file() -> str | None:
    path = _key_file_path()
    try:
        if path.is_file():
            value = _normalize_key(path.read_text(encoding="utf-8"))
            return value or None
    except OSError as exc:
        logger.warning("failed to read encryption key file: %s", exc)
    return None


def _write_key_file(key: str) -> None:
    path = _key_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(key + "\n", encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


async def ensure_encryptor(db: AsyncSession) -> tuple[ConfigEncryptor, bool]:
    """Resolve Fernet key without requiring plaintext master key in system_config.

    Priority:
      1. ENCRYPTION_KEY env / settings
      2. data/.encryption_key file (0600)
      3. Legacy system_config value (migrated out to file, then cleared from DB)
      4. Generate new key → file only
    """
    settings = get_settings()
    created = False
    key = _normalize_key(getattr(settings, "encryption_key", "") or "")
    source = "env" if key else ""

    if not key:
        file_key = _read_key_file()
        if file_key:
            key = file_key
            source = "file"

    entry = await db.get(SystemConfig, LEGACY_DB_KEY)
    if not key and entry is not None and entry.value:
        key = _normalize_key(entry.value)
        source = "db_legacy"
        # Migrate out of DB so backups/ghost no longer carry the master key.
        try:
            _write_key_file(key)
            entry.value = ""
            entry.updated_at = utcnow_iso()
            await db.flush()
            logger.warning(
                "migrated encryption key from system_config to %s; set ENCRYPTION_KEY for production",
                _key_file_path(),
            )
            source = "file_migrated"
        except OSError as exc:
            logger.error("failed to migrate encryption key to file: %s", exc)

    if not key:
        key = ConfigEncryptor.generate_key().decode("utf-8")
        created = True
        try:
            _write_key_file(key)
            source = "generated_file"
        except OSError:
            # Last resort for environments without writable data dir (should be rare).
            if entry is None:
                entry = SystemConfig(
                    key=LEGACY_DB_KEY,
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
            source = "generated_db_fallback"
            logger.warning("encryption key stored in DB fallback path — set ENCRYPTION_KEY")

    logger.debug("encryption key source=%s", source)
    return ConfigEncryptor(key.encode("utf-8")), created
