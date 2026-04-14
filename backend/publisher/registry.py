from __future__ import annotations

from backend.publisher.hugo_publisher import HugoPublisher


class PublisherRegistry:
    def __init__(self):
        self._publishers = {"hugo": HugoPublisher()}

    def get(self, name: str):
        return self._publishers[name]
