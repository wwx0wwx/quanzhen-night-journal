from __future__ import annotations

import base64
import hmac
import secrets
import struct
import time
from hashlib import sha1


def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def generate_recovery_codes(count: int = 10) -> list[str]:
    return [f"{secrets.token_hex(4)}-{secrets.token_hex(4)}" for _ in range(count)]


def otpauth_url(secret: str, username: str, *, issuer: str) -> str:
    from urllib.parse import quote, urlencode

    label = f"{issuer}:{username}"
    query = urlencode({"secret": secret, "issuer": issuer, "algorithm": "SHA1", "digits": "6", "period": "30"})
    return f"otpauth://totp/{quote(label)}?{query}"


def totp_code(secret: str, *, for_time: int | None = None, step: int = 30) -> str:
    timestamp = int(for_time if for_time is not None else time.time())
    counter = timestamp // step
    padded = secret + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded.upper())
    digest = hmac.new(key, struct.pack(">Q", counter), sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{value % 1_000_000:06d}"


def verify_totp(secret: str, code: str, *, valid_window: int = 1) -> bool:
    normalized = "".join(ch for ch in str(code or "") if ch.isdigit())
    if len(normalized) != 6:
        return False
    now = int(time.time())
    for offset in range(-valid_window, valid_window + 1):
        if hmac.compare_digest(totp_code(secret, for_time=now + offset * 30), normalized):
            return True
    return False
