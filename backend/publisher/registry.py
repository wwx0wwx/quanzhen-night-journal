from __future__ import annotations

from backend.publisher.hugo_publisher import HugoPublisher


class UnknownPublishTarget(KeyError):
    """Raised when publish_target is not a registered publisher."""


class PublisherRegistry:
    def __init__(self):
        self._publishers = {"hugo": HugoPublisher()}

    def get(self, name: str):
        key = (name or "hugo").strip() or "hugo"
        try:
            return self._publishers[key]
        except KeyError as exc:
            raise UnknownPublishTarget(key) from exc

    def known_targets(self) -> list[str]:
        return sorted(self._publishers.keys())
