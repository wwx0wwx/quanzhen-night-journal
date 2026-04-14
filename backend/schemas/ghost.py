from __future__ import annotations

from pydantic import BaseModel


class GhostExportRequest(BaseModel):
    include_api_keys: bool = False


class GhostPreview(BaseModel):
    filename: str
    manifest: dict
    conflicts: list[str]
