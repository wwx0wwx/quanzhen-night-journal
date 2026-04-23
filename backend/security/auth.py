from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import Settings, get_settings
from backend.database import get_session
from backend.models import SystemConfig, User

UTC = UTC


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: int, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    expire_at = datetime.now(UTC) + timedelta(hours=settings.jwt_expire_hours)
    payload = {"sub": str(user_id), "exp": expire_at, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def should_use_secure_cookie(request: Request, settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip().lower()
    if forwarded_proto:
        return forwarded_proto == "https"

    forwarded = request.headers.get("forwarded", "").lower()
    if "proto=https" in forwarded:
        return True
    if "proto=http" in forwarded:
        return False

    if request.url.scheme:
        return request.url.scheme.lower() == "https"

    return settings.site_base_url.strip().lower().startswith("https://")


def decode_access_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> User:
    settings = get_settings()
    token = request.cookies.get(settings.cookie_name)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not_authenticated")

    try:
        payload = decode_access_token(token, settings)
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token_invalid") from exc

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user_not_found")
    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> User | None:
    settings = get_settings()
    token = request.cookies.get(settings.cookie_name)
    if not token:
        return None
    try:
        payload = decode_access_token(token, settings)
        return await db.get(User, int(payload["sub"]))
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None


async def is_system_initialized(db: AsyncSession) -> bool:
    marker = await db.get(SystemConfig, "system.initialized")
    return bool(marker and marker.value == "1")


async def require_initialized(db: AsyncSession = Depends(get_session)) -> None:
    if not await is_system_initialized(db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="system_not_initialized")
