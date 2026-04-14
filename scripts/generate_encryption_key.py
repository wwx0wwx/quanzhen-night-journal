from __future__ import annotations

from backend.security.encryption import ConfigEncryptor


if __name__ == "__main__":
    print(ConfigEncryptor.generate_key().decode("utf-8"))
