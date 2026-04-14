from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse


def success(data: Any = None, message: str = "ok") -> JSONResponse:
    return JSONResponse({"code": 0, "message": message, "data": data})


def error(
    code: int,
    message: str,
    data: Any = None,
    status_code: int = 400,
) -> JSONResponse:
    return JSONResponse(
        {"code": code, "message": message, "data": data},
        status_code=status_code,
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
