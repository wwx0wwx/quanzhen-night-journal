from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_orchestrator, get_qa_engine
from backend.api.serializers import post_to_dict
from backend.database import get_session
from backend.engine.digital_stamp import DigitalStampGenerator
from backend.engine.generation_orchestrator import GenerationOrchestrator
from backend.engine.qa_engine import QAEngine
from backend.models import GenerationTask, Post, PostRevision
from backend.publisher.registry import PublisherRegistry
from backend.schemas.post import PostCreate, PostUpdate
from backend.security.auth import get_current_user
from backend.utils.audit import log_audit
from backend.utils.post_content import derive_summary, extract_title, normalize_title
from backend.utils.response import error, paginated, success
from backend.utils.serde import json_dumps
from backend.utils.slug import is_placeholder_slug, slugify
from backend.utils.text_integrity import sanitize_plain_text
from backend.utils.time import utcnow_iso

router = APIRouter()


async def _create_revision(db: AsyncSession, post: Post, reason: str) -> None:
    revision = PostRevision(
        post_id=post.id,
        revision=post.revision,
        title=post.title,
        content_markdown=post.content_markdown,
        front_matter=post.front_matter,
        change_reason=reason,
        created_at=utcnow_iso(),
    )
    db.add(revision)
    await db.flush()


async def _ensure_unique_slug(db: AsyncSession, base_slug: str, *, exclude_post_id: int | None = None) -> str:
    candidate = base_slug
    suffix = 2
    while True:
        stmt = select(Post.id).where(Post.slug == candidate)
        if exclude_post_id is not None:
            stmt = stmt.where(Post.id != exclude_post_id)
        existing = await db.scalar(stmt)
        if existing is None:
            return candidate
        candidate = f"{base_slug}-{suffix}"
        suffix += 1


def _resolve_title(title: str | None, content_markdown: str) -> str:
    explicit_title = normalize_title(title)
    if explicit_title:
        return sanitize_plain_text(explicit_title, max_length=64)
    return sanitize_plain_text(extract_title(content_markdown), max_length=64)


async def _resolve_slug(
    db: AsyncSession,
    *,
    title: str,
    requested_slug: str | None,
    exclude_post_id: int | None = None,
) -> str:
    source = requested_slug.strip() if requested_slug is not None else ""
    if is_placeholder_slug(source):
        source = ""
    base_slug = slugify(source or title, fallback_prefix="post")
    return await _ensure_unique_slug(db, base_slug, exclude_post_id=exclude_post_id)


async def _build_task_map(db: AsyncSession, task_ids: list[int]) -> dict[int, GenerationTask]:
    if not task_ids:
        return {}
    rows = await db.scalars(select(GenerationTask).where(GenerationTask.id.in_(task_ids)))
    return {row.id: row for row in rows}


def _serialize_post(post: Post, task: GenerationTask | None = None) -> dict:
    data = post_to_dict(post, task)
    data["task_status"] = task.status if task else None
    data["task_error_code"] = task.error_code if task else None
    data["task_error_message"] = task.error_message if task else None
    data["queue_wait_ms"] = task.queue_wait_ms if task else None
    return data


@router.get("")
async def list_posts(
    status: str | None = None,
    q: str | None = None,
    sort: str = Query("updated_desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    stmt = select(Post)
    count_stmt = select(func.count()).select_from(Post)
    if status:
        stmt = stmt.where(Post.status == status)
        count_stmt = count_stmt.where(Post.status == status)
    keyword = (q or "").strip()
    if keyword:
        pattern = f"%{keyword}%"
        search_filter = or_(Post.title.ilike(pattern), Post.slug.ilike(pattern), Post.summary.ilike(pattern))
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    order_map = {
        "updated_desc": desc(Post.updated_at),
        "updated_asc": asc(Post.updated_at),
        "published_desc": desc(Post.published_at),
        "published_asc": asc(Post.published_at),
        "created_desc": desc(Post.created_at),
        "created_asc": asc(Post.created_at),
    }
    stmt = (
        stmt.order_by(order_map.get(sort, desc(Post.updated_at)), Post.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = list(await db.scalars(stmt))
    total = await db.scalar(count_stmt) or 0
    task_map = await _build_task_map(db, [item.task_id for item in rows if item.task_id])
    return paginated([_serialize_post(item, task_map.get(item.task_id)) for item in rows], int(total), page, page_size)


@router.post("")
async def create_post(
    payload: PostCreate,
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    now = utcnow_iso()
    title = _resolve_title(payload.title, payload.content_markdown)
    slug = await _resolve_slug(db, title=title, requested_slug=payload.slug)
    summary = sanitize_plain_text(
        payload.summary.strip() or derive_summary(payload.content_markdown, title=title), max_length=180
    )
    post = Post(
        title=title,
        slug=slug,
        front_matter=json_dumps(payload.front_matter),
        content_markdown=payload.content_markdown,
        summary=summary,
        status=payload.status,
        persona_id=payload.persona_id,
        task_id=None,
        published_at=None,
        revision=1,
        publish_target=payload.publish_target,
        digital_stamp=DigitalStampGenerator().generate(payload.content_markdown, title),
        review_info=json_dumps(payload.review_info),
        created_at=now,
        updated_at=now,
    )
    db.add(post)
    await db.flush()
    await log_audit(db, "user", "post.create", "post", str(post.id))
    await db.commit()
    return success(_serialize_post(post))


@router.get("/{post_id}")
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    post = await db.get(Post, post_id)
    if post is None:
        return error(1002, "文章不存在", status_code=404)
    task = await db.get(GenerationTask, post.task_id) if post.task_id else None
    return success(_serialize_post(post, task))


@router.put("/{post_id}")
async def update_post(
    post_id: int,
    payload: PostUpdate,
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    post = await db.get(Post, post_id)
    if post is None:
        return error(1002, "文章不存在", status_code=404)
    await _create_revision(db, post, "manual_update")
    data = payload.model_dump(exclude_none=True)
    for key, value in data.items():
        if key in {"front_matter", "review_info"}:
            setattr(post, key, json_dumps(value))
        else:
            setattr(post, key, value)
    post.title = _resolve_title(post.title, post.content_markdown)
    if "slug" in data:
        post.slug = await _resolve_slug(db, title=post.title, requested_slug=post.slug, exclude_post_id=post.id)
    if "summary" in data and not (post.summary or "").strip():
        post.summary = sanitize_plain_text(derive_summary(post.content_markdown, title=post.title), max_length=180)
    post.revision += 1
    post.updated_at = utcnow_iso()
    post.digital_stamp = DigitalStampGenerator().generate(post.content_markdown, post.title)
    await log_audit(db, "user", "post.update", "post", str(post.id))
    await db.commit()
    task = await db.get(GenerationTask, post.task_id) if post.task_id else None
    return success(_serialize_post(post, task))


@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    post = await db.get(Post, post_id)
    if post is None:
        return error(1002, "文章不存在", status_code=404)
    await db.delete(post)
    await log_audit(db, "user", "post.delete", "post", str(post_id))
    await db.commit()
    return success({"deleted": True})


@router.post("/{post_id}/publish")
async def publish_post(
    post_id: int,
    db: AsyncSession = Depends(get_session),
    qa_engine: QAEngine = Depends(get_qa_engine),
    orchestrator: GenerationOrchestrator = Depends(get_orchestrator),
    _user=Depends(get_current_user),
) -> object:
    post = await db.get(Post, post_id)
    if post is None:
        return error(1002, "文章不存在", status_code=404)
    task = await db.get(GenerationTask, post.task_id) if post.task_id else None
    if task is not None and task.status == "waiting_human_signoff":
        task = await orchestrator.approve_task(task.id, publish_immediately=True)
        post = await db.get(Post, post_id)
        await log_audit(db, "user", "post.publish", "post", str(post.id), {"mode": "task_linked"})
        await db.commit()
        return success(_serialize_post(post, task))
    publisher = PublisherRegistry().get(post.publish_target)
    post.status = "publishing"
    post.updated_at = utcnow_iso()
    await db.commit()
    result = await publisher.publish(post)
    if not result.success:
        post.status = "publish_failed"
        await db.commit()
        return error(4001, "发布失败", {"detail": result.detail}, status_code=500)
    post.status = "published"
    post.published_at = utcnow_iso()
    post.updated_at = post.published_at
    await qa_engine.index_post(post.id, post.content_markdown)
    await log_audit(db, "user", "post.publish", "post", str(post.id))
    await db.commit()
    task = await db.get(GenerationTask, post.task_id) if post.task_id else None
    return success(_serialize_post(post, task))


@router.post("/{post_id}/approve")
async def approve_post(
    post_id: int,
    db: AsyncSession = Depends(get_session),
    orchestrator: GenerationOrchestrator = Depends(get_orchestrator),
    _user=Depends(get_current_user),
) -> object:
    post = await db.get(Post, post_id)
    if post is None:
        return error(1002, "文章不存在", status_code=404)
    task = await db.get(GenerationTask, post.task_id) if post.task_id else None
    if task is not None and task.status == "waiting_human_signoff":
        task = await orchestrator.approve_task(task.id, publish_immediately=False)
        post = await db.get(Post, post_id)
        await log_audit(db, "user", "post.approve", "post", str(post.id), {"mode": "task_linked"})
        await db.commit()
        return success(_serialize_post(post, task))
    post.status = "approved"
    post.updated_at = utcnow_iso()
    await log_audit(db, "user", "post.approve", "post", str(post.id))
    await db.commit()
    task = await db.get(GenerationTask, post.task_id) if post.task_id else None
    return success(_serialize_post(post, task))


@router.post("/{post_id}/archive")
async def archive_post(
    post_id: int,
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    post = await db.get(Post, post_id)
    if post is None:
        return error(1002, "文章不存在", status_code=404)
    post.status = "archived"
    post.updated_at = utcnow_iso()
    await log_audit(db, "user", "post.archive", "post", str(post.id))
    await db.commit()
    task = await db.get(GenerationTask, post.task_id) if post.task_id else None
    return success(_serialize_post(post, task))


@router.get("/{post_id}/revisions")
async def get_revisions(
    post_id: int,
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    rows = await db.scalars(
        select(PostRevision).where(PostRevision.post_id == post_id).order_by(PostRevision.revision.desc())
    )
    return success(
        [
            {
                "id": row.id,
                "post_id": row.post_id,
                "revision": row.revision,
                "title": row.title,
                "content_markdown": row.content_markdown,
                "front_matter": row.front_matter,
                "change_reason": row.change_reason,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    )


@router.post("/{post_id}/revert/{revision}")
async def revert_revision(
    post_id: int,
    revision: int,
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    post = await db.get(Post, post_id)
    if post is None:
        return error(1002, "文章不存在", status_code=404)
    target = await db.scalar(
        select(PostRevision).where(PostRevision.post_id == post_id, PostRevision.revision == revision)
    )
    if target is None:
        return error(1002, "修订版本不存在", status_code=404)
    await _create_revision(db, post, f"revert_to_{revision}")
    post.title = target.title
    post.content_markdown = target.content_markdown
    post.front_matter = target.front_matter
    post.revision += 1
    post.updated_at = utcnow_iso()
    await log_audit(db, "user", "post.revert", "post", str(post.id), {"revision": revision})
    await db.commit()
    task = await db.get(GenerationTask, post.task_id) if post.task_id else None
    return success(_serialize_post(post, task))
