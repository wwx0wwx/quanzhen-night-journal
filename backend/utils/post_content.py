from __future__ import annotations

import re

_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s*")
_LEADING_NOISE_RE = re.compile(r"^[\s\u3000>*`~=_\-+:：;；,，.!！?？、·]+")
_TRAILING_NOISE_RE = re.compile(r"[\s\u3000>*`~=_\-+:：;；,，.!！?？、·]+$")
_SPACE_RE = re.compile(r"\s+")
_SENTENCE_BREAK_RE = re.compile(r"[。！？!?]+")
_TITLE_BREAK_RE = re.compile(r"[。！？!?，,；;：:]")
_GENERIC_TITLES = {
    "夜记",
    "未命名夜记",
    "无题",
    "untitled",
    "night note",
    "night journal",
    "journal",
    "article",
}


def normalize_title(value: str | None, *, max_length: int = 48) -> str:
    text = (value or "").replace("\ufeff", "").strip()
    text = _HEADING_RE.sub("", text)
    text = _LEADING_NOISE_RE.sub("", text)
    text = _TRAILING_NOISE_RE.sub("", text)
    text = _SPACE_RE.sub(" ", text).strip()
    if max_length > 0:
        text = text[:max_length].strip()
    return text


def is_generic_title(title: str | None, *, site_title: str | None = None) -> bool:
    normalized = normalize_title(title, max_length=64)
    if not normalized:
        return True

    if site_title and normalized == normalize_title(site_title, max_length=64):
        return True

    return normalized.casefold() in {item.casefold() for item in _GENERIC_TITLES}


def extract_title(
    content: str,
    *,
    fallback: str = "未命名夜记",
    max_length: int = 48,
    invalid_titles: set[str] | None = None,
) -> str:
    lines = [line.strip() for line in (content or "").splitlines()]
    invalid = {normalize_title(item, max_length=max_length) for item in (invalid_titles or set()) if item}

    for line in lines:
        if not line:
            continue
        if _HEADING_RE.match(line):
            candidate = normalize_title(line, max_length=max_length)
            if candidate and candidate not in invalid:
                return candidate

    for line in lines:
        if not line or line.startswith("```"):
            continue
        candidate = normalize_title(line, max_length=max_length * 2)
        if not candidate or normalize_title(candidate, max_length=max_length) in invalid:
            continue
        segment = _TITLE_BREAK_RE.split(candidate, 1)[0].strip()
        cleaned = normalize_title(segment or candidate, max_length=max_length)
        if cleaned and cleaned not in invalid:
            return cleaned

    return fallback


def derive_summary(content: str, *, title: str | None = None, max_length: int = 140) -> str:
    title = normalize_title(title, max_length=max_length)
    lines = []
    heading_skipped = False

    for raw_line in (content or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("```"):
            continue
        if _HEADING_RE.match(line):
            heading_skipped = True
            continue
        lines.append(line)

    if title and lines:
        first_line = _SPACE_RE.sub(" ", lines[0]).strip()
        if first_line.startswith(title):
            remainder = first_line[len(title) :].lstrip("：:-— ，,。.!！?？；;")
            if len(lines) > 1:
                lines = lines[1:]
            elif remainder:
                lines = [remainder]
            else:
                lines = []

    if not lines:
        source = ""
    else:
        source = " ".join(lines)
    if not source and heading_skipped:
        source = title
    source = _SPACE_RE.sub(" ", source).strip()
    if title and source.startswith(title):
        source = source[len(title) :].lstrip("：:-— ")
    if max_length > 0:
        source = source[:max_length].strip()
    return source or title
