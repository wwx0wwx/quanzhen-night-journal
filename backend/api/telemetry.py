from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session
from backend.models import PublicPageView
from backend.schemas.telemetry import PublicPageViewRequest
from backend.utils.response import success
from backend.utils.time import utcnow_iso


router = APIRouter()


def _client_ip(request: Request) -> str:
    for header in ("cf-connecting-ip", "x-real-ip", "x-forwarded-for"):
        value = request.headers.get(header, "").strip()
        if value:
            return value.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return ""


@router.post("/page-view")
async def track_page_view(
    payload: PublicPageViewRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> object:
    path = (payload.path or "/").strip() or "/"
    if len(path) > 300:
        path = path[:300]
    page_title = (payload.page_title or "").strip()[:200]
    referrer = (payload.referrer or "").strip()[:500]
    user_agent = request.headers.get("user-agent", "").strip()[:500]

    db.add(
        PublicPageView(
            path=path,
            page_title=page_title,
            referrer=referrer,
            ip_address=_client_ip(request),
            user_agent=user_agent,
            created_at=utcnow_iso(),
        )
    )
    await db.commit()
    return success({"tracked": True})
