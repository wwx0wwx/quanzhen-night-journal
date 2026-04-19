from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_config_store
from backend.config import get_settings
from backend.database import get_session
from backend.engine.config_store import ConfigStore
from backend.engine.ghost_manager import GhostManager
from backend.schemas.ghost import GhostExportRequest
from backend.security.auth import get_current_user
from backend.utils.audit import log_audit
from backend.utils.response import error, success


router = APIRouter()
MAX_GHOST_UPLOAD_BYTES = 20 * 1024 * 1024
UPLOAD_READ_CHUNK_BYTES = 1024 * 1024


def _manager(db: AsyncSession, config_store: ConfigStore) -> GhostManager:
    settings = get_settings()
    return GhostManager(db, config_store, settings.ghost_path, settings.database_path.parent / "backups")


async def _read_upload_payload(file: UploadFile) -> tuple[bytes | None, object | None]:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(UPLOAD_READ_CHUNK_BYTES)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_GHOST_UPLOAD_BYTES:
            return None, error(
                1001,
                f"上传文件过大，最大允许 {MAX_GHOST_UPLOAD_BYTES // (1024 * 1024)} MB",
                {"max_bytes": MAX_GHOST_UPLOAD_BYTES},
                status_code=413,
            )
        chunks.append(chunk)
    return b"".join(chunks), None


@router.post("/export")
async def export_ghost(
    payload: GhostExportRequest,
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
    _user=Depends(get_current_user),
) -> object:
    manager = _manager(db, config_store)
    path = await manager.export(include_api_keys=payload.include_api_keys)
    await log_audit(db, "user", "ghost.export", "ghost", path.name)
    await db.commit()
    return success({"filename": path.name, "path": str(path)})


@router.post("/backup-database")
async def backup_database(
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
    _user=Depends(get_current_user),
) -> object:
    manager = _manager(db, config_store)
    path = await manager.backup_database(get_settings().database_path)
    await log_audit(db, "user", "ghost.backup_database", "backup", path.name)
    await db.commit()
    return success({"filename": path.name, "path": str(path)})


@router.post("/preview")
async def preview_ghost(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
    _user=Depends(get_current_user),
) -> object:
    manager = _manager(db, config_store)
    payload, error_response = await _read_upload_payload(file)
    if error_response is not None:
        return error_response
    return success(await manager.preview(file.filename, payload))


@router.post("/import")
async def import_ghost(
    file: UploadFile = File(...),
    confirm: bool = Form(False),
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
    _user=Depends(get_current_user),
) -> object:
    manager = _manager(db, config_store)
    payload, error_response = await _read_upload_payload(file)
    if error_response is not None:
        return error_response
    result = await manager.import_ghost(file.filename, payload, confirm=confirm)
    await log_audit(db, "user", "ghost.import", "ghost", file.filename, {"confirm": confirm})
    await db.commit()
    return success(result)


@router.get("/list")
async def list_ghost_exports(
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
    _user=Depends(get_current_user),
) -> object:
    manager = _manager(db, config_store)
    return success(await manager.list_exports())


@router.delete("/{filename}")
async def delete_ghost_export(
    filename: str,
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
    _user=Depends(get_current_user),
) -> object:
    manager = _manager(db, config_store)
    deleted = await manager.delete_export(filename)
    if deleted is None:
        return error(1002, "Ghost 导出文件不存在", status_code=404)
    await log_audit(db, "user", "ghost.delete_export", "ghost", deleted.name)
    await db.commit()
    return success({"deleted": True, "filename": deleted.name})


@router.get("/database-backups")
async def list_database_backups(
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
    _user=Depends(get_current_user),
) -> object:
    manager = _manager(db, config_store)
    return success(await manager.list_database_backups())


@router.get("/download/{filename}")
async def download_ghost_export(
    filename: str,
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
    _user=Depends(get_current_user),
) -> FileResponse:
    manager = _manager(db, config_store)
    safe_name = Path(filename).name
    target = manager.ghost_dir / safe_name
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="ghost_export_not_found")
    return FileResponse(path=target, filename=safe_name, media_type="application/octet-stream")


@router.get("/download-database-backup/{filename}")
async def download_database_backup(
    filename: str,
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
    _user=Depends(get_current_user),
) -> FileResponse:
    manager = _manager(db, config_store)
    safe_name = Path(filename).name
    target = manager.backup_dir / safe_name
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="database_backup_not_found")
    return FileResponse(path=target, filename=safe_name, media_type="application/octet-stream")
