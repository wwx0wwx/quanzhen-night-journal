from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


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
