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
from backend.utils.response import success


router = APIRouter()


def _manager(db: AsyncSession, config_store: ConfigStore) -> GhostManager:
    return GhostManager(db, config_store, get_settings().ghost_path)


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


@router.post("/preview")
async def preview_ghost(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
    config_store: ConfigStore = Depends(get_config_store),
    _user=Depends(get_current_user),
) -> object:
    manager = _manager(db, config_store)
    payload = await file.read()
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
    payload = await file.read()
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
