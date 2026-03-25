from __future__ import annotations

import json
from typing import Any

from night_journal.config import Settings


class ContentCatalog:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base = settings.automation_dir

    def _load(self, name: str) -> Any:
        return json.loads((self.base / name).read_text(encoding='utf-8'))

    def load_topic_rules(self) -> dict[str, Any]:
        return self._load('topic_rules.json')

    def load_imagery_pool(self) -> dict[str, Any]:
        return self._load('imagery_pool.json')

    def load_scene_pool(self) -> dict[str, Any]:
        return self._load('scene_pool.json')

    def load_emotion_pool(self) -> dict[str, Any]:
        return self._load('emotion_pool.json')

    def load_event_map_rules(self) -> dict[str, Any]:
        return self._load('event_map_rules.json')
