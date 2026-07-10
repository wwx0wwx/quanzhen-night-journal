from __future__ import annotations

import hashlib
import hmac
import time


def verify_bearer(auth_header: str | None, token: str) -> bool:
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return False
    provided = auth_header.split(" ", 1)[1].strip()
    return hmac.compare_digest(provided, token)


def verify_hmac(
    signature_header: str | None,
    body: bytes,
    secret: str,
    *,
    timestamp_header: str | None = None,
    max_skew_seconds: int = 300,
) -> bool:
    """Verify HMAC-SHA256 hex digest of body.

    When ``timestamp_header`` is provided (Unix epoch seconds), reject skew beyond
    ``max_skew_seconds`` to limit replay. Signature may be raw hex or ``sha256=<hex>``.
    """
    if not signature_header:
        return False
    if timestamp_header is not None and str(timestamp_header).strip() != "":
        try:
            ts = int(str(timestamp_header).strip())
        except ValueError:
            return False
        if abs(int(time.time()) - ts) > max_skew_seconds:
            return False
        # Bind timestamp into signed payload when timestamp is supplied.
        signed = f"{ts}.".encode() + body
    else:
        signed = body
    provided = signature_header.strip()
    if provided.lower().startswith("sha256="):
        provided = provided.split("=", 1)[1].strip()
    digest = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(provided, digest)
