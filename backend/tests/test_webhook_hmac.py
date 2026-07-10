from __future__ import annotations

import hashlib
import hmac
import time

from backend.security.webhook_auth import verify_hmac


def test_hmac_accepts_body_only_signature():
    secret = "s3cret"
    body = b'{"source":"x"}'
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_hmac(sig, body, secret) is True
    assert verify_hmac("sha256=" + sig, body, secret) is True


def test_hmac_timestamp_binding_and_skew():
    secret = "s3cret"
    body = b'{"source":"x"}'
    ts = int(time.time())
    signed = f"{ts}.".encode() + body
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    assert verify_hmac(sig, body, secret, timestamp_header=str(ts)) is True
    # raw body-only digest must not verify when timestamp is required by header presence
    bare = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_hmac(bare, body, secret, timestamp_header=str(ts)) is False
    assert verify_hmac(sig, body, secret, timestamp_header=str(ts - 10_000), max_skew_seconds=60) is False
