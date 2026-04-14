from __future__ import annotations

from pydantic import BaseModel


class PublicPageViewRequest(BaseModel):
    path: str = "/"
    page_title: str = ""
    referrer: str = ""
