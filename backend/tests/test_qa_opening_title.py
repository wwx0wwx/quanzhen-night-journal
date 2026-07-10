from __future__ import annotations

import asyncio

from backend.adapters.embedding_adapter import EmbeddingAdapter
from backend.database import get_sessionmaker
from backend.engine.config_store import ConfigStore
from backend.engine.qa_engine import QAEngine
from backend.models import Post
from backend.utils.time import utcnow_iso


def _long_body(seed: str) -> str:
    # Ensure min_length=900 path can still be tested by lowering min in test.
    chunk = f"属下立在风里，王爷的灯还亮着。{seed}袖中手指慢慢收紧。夜色 thrift。"
    # Use Chinese-heavy filler
    filler = "这一夜很静，静到只能听见檐角的风。我把话压回去，只留下半步距离。"
    body = filler * 20
    return f"# {seed}\n\n{body}"


def test_title_duplicate_fails_qa(authed_client):
    async def exercise() -> None:
        session_factory = get_sessionmaker()
        async with session_factory() as db:
            now = utcnow_iso()
            db.add(
                Post(
                    title="夜巡",
                    slug="test-yexun",
                    front_matter="{}",
                    content_markdown=_long_body("夜巡旧稿"),
                    summary="旧稿",
                    status="published",
                    persona_id=1,
                    task_id=None,
                    published_at=now,
                    revision=1,
                    publish_target="hugo",
                    digital_stamp="",
                    review_info="{}",
                    created_at=now,
                    updated_at=now,
                )
            )
            await db.commit()

            config = ConfigStore(db)
            await config.set("qa.min_length", "1", category="qa")
            qa = QAEngine(db, config, EmbeddingAdapter())
            content = (
                "# 夜巡\n\n"
                "我从另一条路回来，看见廊下无人。王爷屋里灯还亮着。"
                "属下把剑横回袖中，没有出声。" * 5
            )
            result = await qa.check(content, persona_id=1)
            assert result["title_ok"] is False
            assert result["title_reason"] == "title_duplicate"
            assert result["passed"] is False

    asyncio.run(exercise())


def test_opening_near_duplicate_fails_qa(authed_client):
    async def exercise() -> None:
        session_factory = get_sessionmaker()
        async with session_factory() as db:
            now = utcnow_iso()
            opening = "残月斜在西边，天还没亮透。我从北山道折回来时，马已疲得发颤。"
            db.add(
                Post(
                    title="残月归",
                    slug="test-canyue",
                    front_matter="{}",
                    content_markdown=f"# 残月归\n\n{opening}廊下一片静。王爷屋里灯还亮着。属下把话压回去。" * 3,
                    summary="旧开场",
                    status="published",
                    persona_id=1,
                    task_id=None,
                    published_at=now,
                    revision=1,
                    publish_target="hugo",
                    digital_stamp="",
                    review_info="{}",
                    created_at=now,
                    updated_at=now,
                )
            )
            await db.commit()

            config = ConfigStore(db)
            await config.set("qa.min_length", "1", category="qa")
            qa = QAEngine(db, config, EmbeddingAdapter())
            content = (
                f"# 夜归\n\n{opening}这一次我换了脚步，却仍听见自己的心跳。属下立在门外。" * 3
            )
            result = await qa.check(content, persona_id=1)
            assert result["opening_ok"] is False
            assert result["opening_reason"] == "opening_near_duplicate"
            assert result["passed"] is False

    asyncio.run(exercise())
