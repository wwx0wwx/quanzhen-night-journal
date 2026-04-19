from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.adapters.embedding_adapter import EmbeddingAdapter, EmbeddingUnavailableError
from backend.engine.config_store import ConfigStore
from backend.models import Post, PostVector
from backend.utils.serde import json_dumps, json_loads


logger = logging.getLogger(__name__)


class QAEngine:
    def __init__(self, db: AsyncSession, config_store: ConfigStore, embedding_adapter: EmbeddingAdapter):
        self.db = db
        self.config_store = config_store
        self.embedding_adapter = embedding_adapter

    async def check(self, content: str, persona_id: int) -> dict:
        length_ok = await self._check_length(content)
        forbidden_ok = await self._check_forbidden(content)
        template_ok = await self._check_template_phrases(content)
        duplicate_result = await self._check_duplicate(content, persona_id)
        duplicate_ok = duplicate_result["duplicate_ok"]
        integrity_ok, integrity_reason = self._check_content_integrity(content)
        risk_level = self._calculate_risk(
            length_ok,
            forbidden_ok,
            template_ok,
            duplicate_ok,
            integrity_ok,
            duplicate_result["duplicate_review_required"],
        )
        return {
            "length_ok": length_ok,
            "forbidden_ok": forbidden_ok,
            "template_ok": template_ok,
            "duplicate_ok": duplicate_ok,
            "duplicate_score": duplicate_result["duplicate_score"],
            "duplicate_post_id": duplicate_result["duplicate_post_id"],
            "duplicate_method": duplicate_result["duplicate_method"],
            "duplicate_reason": duplicate_result["duplicate_reason"],
            "duplicate_review_required": duplicate_result["duplicate_review_required"],
            "integrity_ok": integrity_ok,
            "integrity_reason": integrity_reason,
            "risk_level": risk_level,
            "passed": all(
                [
                    length_ok,
                    forbidden_ok,
                    template_ok,
                    duplicate_ok,
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
        return not any(word and word in content for word in words)

    async def _check_template_phrases(self, content: str) -> bool:
        phrases = json_loads(await self.config_store.get("qa.template_phrases", "[]", decrypt=False), [])
        hits = sum(1 for phrase in phrases if phrase and phrase in content)
        return hits <= 1

    async def _check_duplicate(self, content: str, persona_id: int) -> dict:
        threshold = float(await self.config_store.get("qa.duplicate_threshold", "0.85") or 0.85)
        posts = await self.db.scalars(
            select(Post).where(Post.persona_id == persona_id, Post.status == "published").order_by(Post.id.desc()).limit(20)
        )
        published = list(posts)
        if not published:
            return self._duplicate_result(True, None, None, "embedding", "", False)
        try:
            base_url = await self.config_store.get("embedding.base_url", "") or await self.config_store.get("llm.base_url", "")
            api_key = await self.config_store.get("embedding.api_key", "") or await self.config_store.get("llm.api_key", "")
            model_id = await self.config_store.get("embedding.model_id", "") or await self.config_store.get("llm.model_id", "")
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
                False,
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
        duplicate_ok: bool,
        integrity_ok: bool,
        duplicate_review_required: bool,
    ) -> str:
        if not integrity_ok:
            return "high"
        if duplicate_review_required:
            return "high"
        if not forbidden_ok or not duplicate_ok:
            return "high"
        if not length_ok or not template_ok:
            return "medium"
        return "low"

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
