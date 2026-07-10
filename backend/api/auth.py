from __future__ import annotations

import json

import bcrypt
import jwt
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_encryptor
from backend.config import get_settings
from backend.database import get_session
from backend.models import User
from backend.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    TwoFactorConfirmRequest,
    TwoFactorDisableRequest,
    TwoFactorLoginRequest,
)
from backend.security.auth import (
    create_access_token,
    create_pre_auth_token,
    decode_pre_auth_token,
    get_current_user,
    get_optional_user,
    hash_password,
    is_system_initialized,
    should_use_secure_cookie,
    verify_password,
)
from backend.security.encryption import ConfigEncryptor
from backend.security.totp import generate_recovery_codes, generate_totp_secret, otpauth_url, verify_totp
from backend.utils.audit import log_audit
from backend.utils.response import error, fail, success
from backend.utils.time import utcnow_iso

router = APIRouter()


def _hash_recovery_code(code: str) -> str:
    return bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_recovery_code(code: str, hashed: str) -> bool:
    return bcrypt.checkpw(code.encode("utf-8"), hashed.encode("utf-8"))


def _recovery_hashes(user: User) -> list[str]:
    try:
        return json.loads(user.recovery_codes_hash or "[]")
    except json.JSONDecodeError:
        return []


def _decrypt_totp_secret(user: User, encryptor: ConfigEncryptor) -> str:
    if not user.totp_secret_enc:
        return ""
    return encryptor.decrypt(user.totp_secret_enc)


def _set_login_cookie(response, request: Request, token: str) -> None:
    response.set_cookie(
        key=get_settings().cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=24 * 3600,
        secure=should_use_secure_cookie(request),
    )


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


async def _login_success_response(user: User, request: Request, db: AsyncSession) -> object:
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
    _set_login_cookie(response, request, token)
    return response


@router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> object:
    user = await db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        return fail("invalid_credentials")

    if user.totp_enabled:
        await log_audit(db, "user", "auth.2fa.required", "user", str(user.id), ip=_client_ip(request))
        await db.commit()
        return success(
            {
                "requires_2fa": True,
                "pre_auth_token": create_pre_auth_token(user.id),
                "username": user.username,
            }
        )

    response = await _login_success_response(user, request, db)
    await log_audit(db, "user", "auth.login", "user", str(user.id), ip=request.client.host if request.client else None)
    await db.commit()
    return response


@router.post("/login/2fa")
async def login_2fa(
    payload: TwoFactorLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
    encryptor: ConfigEncryptor = Depends(get_encryptor),
) -> object:
    try:
        user_id = decode_pre_auth_token(payload.pre_auth_token)
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return fail("token_invalid")

    user = await db.get(User, user_id)
    if user is None or not user.totp_enabled:
        return fail("twofa_invalid")

    verified = False
    if payload.code:
        secret = _decrypt_totp_secret(user, encryptor)
        verified = bool(secret and verify_totp(secret, payload.code))
    elif payload.recovery_code:
        hashes = _recovery_hashes(user)
        remaining = []
        for item in hashes:
            if not verified and _verify_recovery_code(payload.recovery_code, item):
                verified = True
                continue
            remaining.append(item)
        if verified:
            user.recovery_codes_hash = json.dumps(remaining)

    if not verified:
        await log_audit(
            db,
            "user",
            "auth.2fa.login_fail",
            "user",
            str(user.id),
            ip=_client_ip(request),
            severity="warning",
        )
        await db.commit()
        return fail("twofa_invalid")

    response = await _login_success_response(user, request, db)
    await log_audit(db, "user", "auth.2fa.login_ok", "user", str(user.id), ip=_client_ip(request))
    await db.commit()
    return response


@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_session),
    user: User | None = Depends(get_optional_user),
) -> object:
    response = success({"logged_out": True})
    response.delete_cookie(
        get_settings().cookie_name,
        httponly=True,
        samesite="lax",
        secure=should_use_secure_cookie(request),
    )
    if user:
        await log_audit(
            db, "user", "auth.logout", "user", str(user.id), ip=request.client.host if request.client else None
        )
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
        return error(1001, "旧密码错误", status_code=400, message_key="errors.raw.old_password_invalid")
    user.password_hash = hash_password(payload.new_password)
    user.is_initialized = 1
    await log_audit(
        db, "user", "auth.change_password", "user", str(user.id), ip=request.client.host if request.client else None
    )
    await db.commit()
    return success({"changed": True})


@router.get("/2fa/status")
async def twofa_status(user: User = Depends(get_current_user)) -> object:
    return success({"enabled": bool(user.totp_enabled), "confirmed": bool(user.totp_confirmed_at)})


@router.post("/2fa/setup")
async def twofa_setup(
    request: Request,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
    encryptor: ConfigEncryptor = Depends(get_encryptor),
) -> object:
    secret = generate_totp_secret()
    recovery_codes = generate_recovery_codes()
    user.totp_enabled = 0
    user.totp_secret_enc = encryptor.encrypt(secret)
    user.totp_confirmed_at = None
    user.recovery_codes_hash = json.dumps([_hash_recovery_code(code) for code in recovery_codes])
    await log_audit(db, "user", "auth.2fa.setup", "user", str(user.id), ip=_client_ip(request))
    await db.commit()
    issuer = "Quanzhen Night Journal"
    return success(
        {
            "otpauth_url": otpauth_url(secret, user.username, issuer=issuer),
            "secret": secret,
            "recovery_codes": recovery_codes,
        }
    )


@router.post("/2fa/confirm")
async def twofa_confirm(
    payload: TwoFactorConfirmRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
    encryptor: ConfigEncryptor = Depends(get_encryptor),
) -> object:
    secret = _decrypt_totp_secret(user, encryptor)
    if not secret or not verify_totp(secret, payload.code):
        await log_audit(
            db,
            "user",
            "auth.2fa.confirm_fail",
            "user",
            str(user.id),
            ip=_client_ip(request),
            severity="warning",
        )
        await db.commit()
        return fail("twofa_invalid")
    user.totp_enabled = 1
    user.totp_confirmed_at = utcnow_iso()
    await log_audit(db, "user", "auth.2fa.confirm", "user", str(user.id), ip=_client_ip(request))
    await db.commit()
    return success({"enabled": True, "confirmed": True})


@router.post("/2fa/disable")
async def twofa_disable(
    payload: TwoFactorDisableRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
    encryptor: ConfigEncryptor = Depends(get_encryptor),
) -> object:
    if not verify_password(payload.password, user.password_hash):
        return error(1001, "密码错误", status_code=400, message_key="errors.raw.password_invalid")
    if user.totp_enabled:
        secret = _decrypt_totp_secret(user, encryptor)
        if secret and not verify_totp(secret, payload.code):
            return fail("twofa_invalid")
    user.totp_enabled = 0
    user.totp_secret_enc = None
    user.totp_confirmed_at = None
    user.recovery_codes_hash = None
    await log_audit(db, "user", "auth.2fa.disable", "user", str(user.id), ip=_client_ip(request))
    await db.commit()
    return success({"enabled": False, "confirmed": False})


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
