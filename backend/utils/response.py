from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from backend.utils.error_catalog import key_for_code


def success(data: Any = None, message: str = "ok") -> JSONResponse:
    return JSONResponse({"code": 0, "message": message, "data": data})


def error(
    code: int,
    message: str,
    data: Any = None,
    status_code: int = 400,
    message_key: str | None = None,
) -> JSONResponse:
    resolved_key = message_key or key_for_code(code)
    return JSONResponse(
        {"code": code, "message": message, "message_key": resolved_key, "data": data},
        status_code=status_code,
    )


def fail(
    error_id: str,
    *,
    data: Any = None,
    status_code: int | None = None,
    message: str | None = None,
) -> JSONResponse:
    from backend.utils.error_catalog import get_error

    meta = get_error(error_id)
    return error(
        int(meta["code"]),
        message or error_id,
        data=data,
        status_code=status_code or int(meta["http"]),
        message_key=str(meta["key"]),
    )


def paginated(items: list[Any], total: int, page: int, page_size: int) -> JSONResponse:
    return success(
        {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )
