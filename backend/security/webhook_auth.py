from __future__ import annotations

import hashlib
import hmac


def verify_bearer(auth_header: str | None, token: str) -> bool:
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return False
    provided = auth_header.split(" ", 1)[1].strip()
    return hmac.compare_digest(provided, token)


def verify_hmac(signature_header: str | None, body: bytes, secret: str) -> bool:
    if not signature_header:
        return False
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature_header, digest)
