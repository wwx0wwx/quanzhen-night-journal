from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from backend.models import Post


@dataclass(slots=True)
class PublishResult:
    success: bool
    url: str = ""
    detail: str = ""


class PublisherAdapter(ABC):
    @abstractmethod
    async def publish(self, post: Post) -> PublishResult: ...

    @abstractmethod
    async def unpublish(self, post: Post) -> None: ...

    @abstractmethod
    async def health_check(self) -> bool: ...
