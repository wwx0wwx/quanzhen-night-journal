from __future__ import annotations

import logging
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.adapters.embedding_adapter import EmbeddingAdapter, EmbeddingUnavailableError
from backend.engine.config_store import ConfigStore
from backend.models import Post, PostVector
from backend.utils.content_signals import body_text as article_body_text
from backend.utils.content_signals import extract_ending, extract_motifs, extract_opening, shared_ngram
from backend.utils.post_content import extract_title, normalize_title
from backend.utils.serde import json_dumps, json_loads

logger = logging.getLogger(__name__)

FIRST_PERSON_MARKERS = ("我", "属下", "在下", "末将", "卑职", "小人", "奴婢")
SECOND_PERSON_MARKERS = ("你", "您")
ENGLISH_FIRST_PERSON_RE = re.compile(r"\b(i|me|my|mine|we|us|our|ours)\b", re.IGNORECASE)
ENGLISH_SECOND_PERSON_RE = re.compile(r"\b(you|your|yours)\b", re.IGNORECASE)
DIALOGUE_RE = re.compile(
    r"“[^”]{0,600}”|「[^」]{0,600}」|『[^』]{0,600}』|‘[^’]{0,600}’|\"[^\"]{0,600}\"|'[^']{0,600}'",
    re.DOTALL,
)
LOW_SIGNAL_MOTIFS = {"王爷", "姐姐", "深夜", "灯影", "风雨", "霜雪"}


class QAEngine:
    def __init__(self, db: AsyncSession, config_store: ConfigStore, embedding_adapter: EmbeddingAdapter):
        self.db = db
        self.config_store = config_store
        self.embedding_adapter = embedding_adapter

    async def check(self, content: str, persona_id: int) -> dict:
        length_ok = await self._check_length(content)
        forbidden_ok = await self._check_forbidden(content)
        template_ok = await self._check_template_phrases(content)
        language_ok = await self._check_language(content)
        perspective_ok, perspective_reason = await self._check_perspective(content)
        format_ok, format_reason = await self._check_format(content)
        duplicate_result = await self._check_duplicate(content, persona_id)
        duplicate_ok = duplicate_result["duplicate_ok"]
        novelty_result = await self._check_novelty(content, persona_id)
        novelty_ok = novelty_result["novelty_ok"]
        integrity_ok, integrity_reason = self._check_content_integrity(content)
        risk_level = self._calculate_risk(
            length_ok,
            forbidden_ok,
            template_ok,
            language_ok,
            perspective_ok,
            format_ok,
            duplicate_ok,
            novelty_ok,
            integrity_ok,
            duplicate_result["duplicate_review_required"],
        )
        return {
            "length_ok": length_ok,
            "forbidden_ok": forbidden_ok,
            "template_ok": template_ok,
            "language_ok": language_ok,
            "perspective_ok": perspective_ok,
            "perspective_reason": perspective_reason,
            "format_ok": format_ok,
            "format_reason": format_reason,
            "duplicate_ok": duplicate_ok,
            "duplicate_score": duplicate_result["duplicate_score"],
            "duplicate_post_id": duplicate_result["duplicate_post_id"],
            "duplicate_method": duplicate_result["duplicate_method"],
            "duplicate_reason": duplicate_result["duplicate_reason"],
            "duplicate_review_required": duplicate_result["duplicate_review_required"],
            "novelty_ok": novelty_ok,
            "novelty_reason": novelty_result["novelty_reason"],
            "novelty_post_id": novelty_result["novelty_post_id"],
            "novelty_evidence": novelty_result["novelty_evidence"],
            "novelty_method": novelty_result["novelty_method"],
            "integrity_ok": integrity_ok,
            "integrity_reason": integrity_reason,
            "risk_level": risk_level,
            "passed": all(
                [
                    length_ok,
                    forbidden_ok,
                    template_ok,
                    language_ok,
                    perspective_ok,
                    format_ok,
                    novelty_ok,
                    integrity_ok,
                    not duplicate_result["duplicate_review_required"],
                ]
            ),
        }

    async def index_post(self, post_id: int, content: str) -> None:
        base_url = await self.config_store.get("embedding.base_url", "")
        api_key = await self.config_store.get("embedding.api_key", "")
        model_id = await self.config_store.get("embedding.model_id", "")
        try:
            vector = (
                await self.embedding_adapter.embed(
                    base_url=base_url or "",
                    api_key=api_key or "",
                    model_id=model_id or "",
                    texts=[content],
                )
            )[0]
        except EmbeddingUnavailableError:
            return
        existing = await self.db.get(PostVector, post_id)
        if existing is None:
            self.db.add(PostVector(post_id=post_id, embedding=json_dumps(vector)))
        else:
            existing.embedding = json_dumps(vector)
        await self.db.flush()

    async def _check_length(self, content: str) -> bool:
        min_length = int(await self.config_store.get("qa.min_length", "200") or 200)
        max_length = int(await self.config_store.get("qa.max_length", "5000") or 5000)
        length = len(content.strip())
        return min_length <= length <= max_length

    async def _check_forbidden(self, content: str) -> bool:
        words = json_loads(await self.config_store.get("qa.forbidden_words", "[]", decrypt=False), [])
        content_lower = content.lower()
        return not any(word and word.lower() in content_lower for word in words)

    async def _check_template_phrases(self, content: str) -> bool:
        phrases = json_loads(await self.config_store.get("qa.template_phrases", "[]", decrypt=False), [])
        hits = sum(1 for phrase in phrases if phrase and phrase in content)
        return hits <= 1

    async def _check_language(self, content: str) -> bool:
        required = (await self.config_store.get("qa.required_language", "zh") or "zh").strip().lower()
        if required == "any":
            return True

        cjk_count = sum(1 for char in content if "\u4e00" <= char <= "\u9fff")
        latin_count = sum(1 for char in content if ("a" <= char.lower() <= "z"))
        if required == "zh":
            return cjk_count >= 20 and cjk_count >= latin_count
        if required == "en":
            return latin_count >= 20 and latin_count >= cjk_count * 2
        return True

    async def _check_perspective(self, content: str) -> tuple[bool, str]:
        required = (await self.config_store.get("qa.required_perspective", "first_person") or "first_person").strip()
        if required == "any":
            return True, ""

        body = self._strip_dialogue(self._body_text(content))
        second_person_count = sum(body.count(marker) for marker in SECOND_PERSON_MARKERS)
        if second_person_count or ENGLISH_SECOND_PERSON_RE.search(body):
            return False, "second_person_pronoun_detected"

        first_person_count = sum(body.count(marker) for marker in FIRST_PERSON_MARKERS)
        if first_person_count == 0 and not ENGLISH_FIRST_PERSON_RE.search(body):
            return False, "first_person_marker_missing"

        return True, ""

    async def _check_format(self, content: str) -> tuple[bool, str]:
        invalid_titles = {"夜记", "无题", "未命名", "未命名夜记"}
        site_title = (await self.config_store.get("site.title", "") or "").strip()
        if site_title:
            invalid_titles.add(site_title)

        lines = content.splitlines()
        first_index = next((index for index, line in enumerate(lines) if line.strip()), None)
        if first_index is None:
            return False, "empty_content"

        first_line = lines[first_index].strip()
        if not first_line.startswith("# ") or first_line.startswith("##"):
            return False, "missing_markdown_h1"

        title = normalize_title(first_line, max_length=64)
        if not title:
            return False, "empty_markdown_h1"
        if title in invalid_titles:
            derived_title = extract_title(content, invalid_titles=invalid_titles)
            if normalize_title(derived_title, max_length=64) in invalid_titles:
                return False, "generic_markdown_h1"
        if first_index + 1 >= len(lines) or lines[first_index + 1].strip():
            return False, "missing_blank_line_after_h1"
        return True, ""

    def _body_text(self, content: str) -> str:
        return article_body_text(content)

    def _strip_dialogue(self, text: str) -> str:
        return DIALOGUE_RE.sub("", text)

    async def _check_duplicate(self, content: str, persona_id: int) -> dict:
        threshold = float(await self.config_store.get("qa.duplicate_threshold", "0.85") or 0.85)
        block_threshold = float(await self.config_store.get("qa.duplicate_block_threshold", "0.92") or 0.92)
        block_threshold = max(threshold, block_threshold)
        posts = await self.db.scalars(
            select(Post)
            .where(Post.persona_id == persona_id, Post.status == "published")
            .order_by(Post.id.desc())
            .limit(20)
        )
        published = list(posts)
        if not published:
            return self._duplicate_result(True, None, None, "embedding", "", False)
        try:
            base_url = await self.config_store.get("embedding.base_url", "") or await self.config_store.get(
                "llm.base_url", ""
            )
            api_key = await self.config_store.get("embedding.api_key", "") or await self.config_store.get(
                "llm.api_key", ""
            )
            model_id = await self.config_store.get("embedding.model_id", "") or await self.config_store.get(
                "llm.model_id", ""
            )
            content_vector = (
                await self.embedding_adapter.embed(
                    base_url=base_url or "",
                    api_key=api_key or "",
                    model_id=model_id or "",
                    texts=[content],
                )
            )[0]
            candidate_post_ids = [post.id for post in published]
            vectors = await self.db.scalars(select(PostVector).where(PostVector.post_id.in_(candidate_post_ids)))
            vector_map = {item.post_id: json_loads(item.embedding, []) for item in vectors}
            best_post_id = None
            best_score = 0.0
            for post in published:
                score = self.embedding_adapter.cosine_similarity(content_vector, vector_map.get(post.id, []))
                if score > best_score:
                    best_score = score
                    best_post_id = post.id
            return self._duplicate_result(
                best_score <= threshold,
                best_score,
                best_post_id,
                "embedding",
                "",
                best_score > block_threshold,
            )
        except (EmbeddingUnavailableError, ValueError, TypeError, KeyError) as exc:
            logger.warning("duplicate-check fallback engaged: %s", exc)
            overlap, post_id = self._fallback_duplicate_score(content, published)
            return self._duplicate_result(
                overlap <= threshold,
                overlap,
                post_id,
                "fallback/manual_review",
                str(exc).strip() or exc.__class__.__name__,
                True,
            )

    async def _check_novelty(self, content: str, persona_id: int) -> dict:
        posts = await self.db.scalars(
            select(Post)
            .where(Post.persona_id == persona_id, Post.status == "published")
            .order_by(Post.id.desc())
            .limit(50)
        )
        published = list(posts)
        if not published:
            return self._novelty_result(True, "", None, "", "local")

        title = normalize_title(extract_title(content, fallback=""), max_length=64)
        if title:
            for post in published:
                if title == normalize_title(post.title, max_length=64):
                    return self._novelty_result(False, "title_reused", post.id, title, "title")

        opening = extract_opening(content, limit=180)
        ending = extract_ending(content, limit=160)
        body = article_body_text(content)[:4000]
        signature = self._signature_motifs(extract_motifs(content, title=title, limit=20))

        for post in published:
            old_content = post.content_markdown or ""
            old_opening = extract_opening(old_content, limit=200)
            opening_overlap = shared_ngram(opening, old_opening, min_length=18, max_length=36)
            if opening_overlap:
                return self._novelty_result(
                    False,
                    "opening_reused",
                    post.id,
                    opening_overlap,
                    "opening_ngram",
                )

            old_ending = extract_ending(old_content, limit=180)
            ending_overlap = shared_ngram(ending, old_ending, min_length=18, max_length=32)
            if ending_overlap:
                return self._novelty_result(
                    False,
                    "ending_reused",
                    post.id,
                    ending_overlap,
                    "ending_ngram",
                )

            body_overlap = shared_ngram(body, old_content[:4000], min_length=34, max_length=52)
            if body_overlap:
                return self._novelty_result(
                    False,
                    "long_phrase_reused",
                    post.id,
                    body_overlap,
                    "body_ngram",
                )

            old_signature = self._signature_motifs(extract_motifs(old_content, title=post.title, limit=20))
            shared_motifs = sorted(signature & old_signature)
            if len(shared_motifs) >= 4:
                return self._novelty_result(
                    False,
                    "scene_signature_reused",
                    post.id,
                    "、".join(shared_motifs),
                    "motif_signature",
                )

        return self._novelty_result(True, "", None, "", "local")

    def _check_content_integrity(self, content: str) -> tuple[bool, str]:
        visible = [char for char in content if not char.isspace()]
        if not visible:
            return False, "empty_content"

        placeholder_count = sum(1 for char in visible if char in {"?", "�"})
        readable_count = sum(1 for char in visible if char.isalnum() or "\u4e00" <= char <= "\u9fff")
        placeholder_ratio = placeholder_count / max(1, len(visible))

        if "�" in content:
            return False, "replacement_character_detected"
        if placeholder_count >= 12 and placeholder_ratio >= 0.25 and readable_count <= placeholder_count:
            return False, "placeholder_question_marks_detected"
        return True, ""

    def _calculate_risk(
        self,
        length_ok: bool,
        forbidden_ok: bool,
        template_ok: bool,
        language_ok: bool,
        perspective_ok: bool,
        format_ok: bool,
        duplicate_ok: bool,
        novelty_ok: bool,
        integrity_ok: bool,
        duplicate_review_required: bool,
    ) -> str:
        if not integrity_ok:
            return "high"
        if not language_ok:
            return "high"
        if not perspective_ok:
            return "high"
        if not format_ok:
            return "medium"
        if duplicate_review_required:
            return "high"
        if not forbidden_ok:
            return "high"
        if not duplicate_ok:
            return "medium"
        if not novelty_ok:
            return "medium"
        if not length_ok or not template_ok:
            return "medium"
        return "low"

    def _signature_motifs(self, motifs: list[str]) -> set[str]:
        return {motif for motif in motifs if motif not in LOW_SIGNAL_MOTIFS}

    def _fallback_duplicate_score(self, content: str, published: list[Post]) -> tuple[float, int | None]:
        normalized = set(content.split())
        best_overlap = 0.0
        best_post_id = None
        for post in published:
            tokens = set(post.content_markdown.split())
            overlap = len(normalized & tokens) / max(1, len(normalized | tokens))
            if overlap > best_overlap:
                best_overlap = overlap
                best_post_id = post.id
        return best_overlap, best_post_id

    def _duplicate_result(
        self,
        duplicate_ok: bool,
        duplicate_score: float | None,
        duplicate_post_id: int | None,
        duplicate_method: str,
        duplicate_reason: str,
        duplicate_review_required: bool,
    ) -> dict:
        return {
            "duplicate_ok": duplicate_ok,
            "duplicate_score": round(float(duplicate_score), 4) if duplicate_score is not None else None,
            "duplicate_post_id": duplicate_post_id,
            "duplicate_method": duplicate_method,
            "duplicate_reason": duplicate_reason,
            "duplicate_review_required": duplicate_review_required,
        }

    def _novelty_result(
        self,
        novelty_ok: bool,
        novelty_reason: str,
        novelty_post_id: int | None,
        novelty_evidence: str,
        novelty_method: str,
    ) -> dict:
        return {
            "novelty_ok": novelty_ok,
            "novelty_reason": novelty_reason,
            "novelty_post_id": novelty_post_id,
            "novelty_evidence": novelty_evidence[:80],
            "novelty_method": novelty_method,
        }
