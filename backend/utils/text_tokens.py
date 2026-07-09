from __future__ import annotations

import re

_ASCII_TOKEN_RE = re.compile(r"[a-z0-9_]{2,}", re.IGNORECASE)
_CJK_CHAR_RE = re.compile(r"[\u4e00-\u9fff]")


def tokenize_for_search(text: str, *, max_tokens: int = 64) -> list[str]:
    """Tokenize mixed Chinese/English text for keyword fallback search.

    Strategy:
    - ASCII words of length >= 2
    - CJK unigrams and bigrams (common for Chinese retrieval without jieba)
    """
    if not text:
        return []

    normalized = text.strip().lower()
    if not normalized:
        return []

    tokens: list[str] = []
    seen: set[str] = set()

    def add(token: str) -> None:
        token = token.strip()
        if not token or token in seen:
            return
        seen.add(token)
        tokens.append(token)

    for match in _ASCII_TOKEN_RE.finditer(normalized):
        add(match.group(0))
        if len(tokens) >= max_tokens:
            return tokens

    # Strip ASCII runs so CJK windows are cleaner.
    cjk_only = _ASCII_TOKEN_RE.sub(" ", normalized)
    cjk_chars = _CJK_CHAR_RE.findall(cjk_only)
    for char in cjk_chars:
        add(char)
        if len(tokens) >= max_tokens:
            return tokens
    for index in range(len(cjk_chars) - 1):
        add(cjk_chars[index] + cjk_chars[index + 1])
        if len(tokens) >= max_tokens:
            return tokens

    # Keep explicit whitespace tokens for already-segmented queries.
    for part in normalized.split():
        add(part)
        if len(tokens) >= max_tokens:
            break

    return tokens


def token_overlap_score(query: str, document: str) -> float:
    query_tokens = set(tokenize_for_search(query))
    if not query_tokens:
        return 0.0
    doc_tokens = set(tokenize_for_search(document, max_tokens=256))
    if not doc_tokens:
        return 0.0
    overlap = len(query_tokens & doc_tokens)
    if not overlap:
        # Substring fallback for short CJK queries that still appear in the document.
        substring_hits = sum(1 for token in query_tokens if token in document.lower())
        if not substring_hits:
            return 0.0
        return substring_hits / max(1, len(query_tokens))
    return overlap / max(1, len(query_tokens | doc_tokens))
