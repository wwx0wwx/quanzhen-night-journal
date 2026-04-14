from __future__ import annotations

import html
import re
from dataclasses import dataclass


_HTML_TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")
_SPACE_RE = re.compile(r"\s+")


@dataclass(slots=True)
class TextIntegrityIssue:
    code: str
    detail: str


def inspect_text_integrity(value: str | None) -> list[TextIntegrityIssue]:
    text = (value or "").replace("\ufeff", "")
    visible = [char for char in text if not char.isspace()]
    if not visible:
        return []

    issues: list[TextIntegrityIssue] = []
    if "\ufffd" in text:
        issues.append(TextIntegrityIssue("replacement_character_detected", "contains U+FFFD replacement character"))

    placeholder_count = sum(1 for char in visible if char == "?")
    readable_count = sum(1 for char in visible if char.isalnum() or "\u4e00" <= char <= "\u9fff")
    placeholder_ratio = placeholder_count / max(1, len(visible))

    if placeholder_count >= 2 and placeholder_ratio >= 0.35 and readable_count <= placeholder_count:
        issues.append(TextIntegrityIssue("placeholder_question_marks_detected", "contains too many placeholder question marks"))
    return issues


def ensure_text_integrity(value: str | None, field_name: str) -> str:
    text = value or ""
    issues = inspect_text_integrity(text)
    if issues:
        raise ValueError(f"{field_name}:{issues[0].code}")
    return text


def sanitize_plain_text(value: str | None, *, max_length: int = 0) -> str:
    text = html.unescape((value or "").replace("\x00", "").replace("\ufeff", ""))
    text = _HTML_TAG_RE.sub("", text)
    text = _SPACE_RE.sub(" ", text).strip()
    if max_length > 0:
        text = text[:max_length].strip()
    return text

