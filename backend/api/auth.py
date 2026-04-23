from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.database import get_session
from backend.models import User
from backend.security.auth import (
    create_access_token,
    get_current_user,
    get_optional_user,
    hash_password,
    is_system_initialized,
    verify_password,
)
from backend.schemas.auth import ChangePasswordRequest, LoginRequest
from backend.utils.audit import log_audit
from backend.utils.response import error, success


router = APIRouter()


@router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> object:
    user = await db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        return error(2001, "用户名或密码错误", status_code=401)

    system_initialized = await is_system_initialized(db)
    token = create_access_token(user.id)
    response = success(
        {
            "is_logged_in": True,
            "is_initialized": system_initialized,
            "system_initialized": system_initialized,
            "username": user.username,
        }
    )
    response.set_cookie(
        key=get_settings().cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=24 * 3600,
        secure=get_settings().is_production,
    )
    await log_audit(db, "user", "auth.login", "user", str(user.id), ip=request.client.host if request.client else None)
    await db.commit()
    return response


@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_session),
    user: User | None = Depends(get_optional_user),
) -> object:
    response = success({"logged_out": True})
    response.delete_cookie(get_settings().cookie_name)
    if user:
        await log_audit(db, "user", "auth.logout", "user", str(user.id), ip=request.client.host if request.client else None)
        await db.commit()
    return response


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> object:
    if not verify_password(payload.old_password, user.password_hash):
        return error(1001, "旧密码错误", status_code=400)
    user.password_hash = hash_password(payload.new_password)
    user.is_initialized = 1
    await log_audit(db, "user", "auth.change_password", "user", str(user.id), ip=request.client.host if request.client else None)
    await db.commit()
    return success({"changed": True})


@router.get("/status")
async def auth_status(
    db: AsyncSession = Depends(get_session),
    user: User | None = Depends(get_optional_user),
) -> object:
    system_initialized = await is_system_initialized(db)
    return success(
        {
            "is_logged_in": user is not None,
            "is_initialized": system_initialized,
            "system_initialized": system_initialized,
            "username": user.username if user else None,
        }
    )
