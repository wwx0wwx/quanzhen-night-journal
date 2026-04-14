from __future__ import annotations

import re


_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s*")
_LEADING_NOISE_RE = re.compile(r"^[\s\u3000>*`~=_\-+:：;；,，.!！?？、·]+")
_TRAILING_NOISE_RE = re.compile(r"[\s\u3000>*`~=_\-+:：;；,，.!！?？、·]+$")
_SPACE_RE = re.compile(r"\s+")
_SENTENCE_BREAK_RE = re.compile(r"[。！？!?]+")


def normalize_title(value: str | None, *, max_length: int = 48) -> str:
    text = (value or "").replace("\ufeff", "").strip()
    text = _HEADING_RE.sub("", text)
    text = _LEADING_NOISE_RE.sub("", text)
    text = _TRAILING_NOISE_RE.sub("", text)
    text = _SPACE_RE.sub(" ", text).strip()
    if max_length > 0:
        text = text[:max_length].strip()
    return text


def extract_title(content: str, *, fallback: str = "未命名夜记", max_length: int = 48) -> str:
    lines = [line.strip() for line in (content or "").splitlines()]

    for line in lines:
        if not line:
            continue
        if _HEADING_RE.match(line):
            candidate = normalize_title(line, max_length=max_length)
            if candidate:
                return candidate

    for line in lines:
        if not line or line.startswith("```"):
            continue
        candidate = normalize_title(line, max_length=max_length * 2)
        if not candidate:
            continue
        segment = _SENTENCE_BREAK_RE.split(candidate, 1)[0].strip()
        cleaned = normalize_title(segment or candidate, max_length=max_length)
        if cleaned:
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
