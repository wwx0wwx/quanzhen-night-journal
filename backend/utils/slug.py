from __future__ import annotations

import hashlib
import re
import unicodedata

_DASH_RE = re.compile(r"-{2,}")
_PLACEHOLDER_SLUG_RE = re.compile(r"^(?:\d+-)?untitled(?:-\d+)?$", re.IGNORECASE)


def slugify(value: str, *, fallback_prefix: str = "note", max_length: int = 80) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    parts: list[str] = []
    last_was_dash = False

    for char in text.strip():
        category = unicodedata.category(char)
        if char.isascii() and char.isalnum():
            parts.append(char.lower())
            last_was_dash = False
            continue
        if category[:1] in {"L", "N"}:
            parts.append(char.lower() if category.startswith("L") else char)
            last_was_dash = False
            continue
        if parts and not last_was_dash:
            parts.append("-")
            last_was_dash = True

    slug = _DASH_RE.sub("-", "".join(parts)).strip("-")
    if max_length > 0 and len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")
    if slug:
        return slug

    prefix = re.sub(r"[^a-z0-9]+", "-", fallback_prefix.lower()).strip("-") or "note"
    suffix_seed = text.strip() or "empty"
    suffix = hashlib.sha1(suffix_seed.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}-{suffix}"


def is_placeholder_slug(value: str | None) -> bool:
    slug = (value or "").strip().strip("-")
    if not slug:
        return True
    return bool(_PLACEHOLDER_SLUG_RE.match(slug))
