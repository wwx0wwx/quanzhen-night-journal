from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Settings:
    engine_root: Path
    automation_dir: Path
    content_dir: Path
    draft_review_dir: Path
    output_dir: Path
    log_dir: Path
    openai_api_key: str
    openai_base_url: str
    openai_model: str


def load_settings(env_root: Optional[Path] = None) -> Settings:
    root = Path(env_root or os.getenv('ENGINE_ROOT', Path(__file__).resolve().parent.parent)).resolve()
    return Settings(
        engine_root=root,
        automation_dir=root / 'automation',
        content_dir=root / 'content' / 'posts',
        draft_review_dir=root / 'draft_review',
        output_dir=Path(os.getenv('BLOG_OUTPUT_DIR', '/var/www/example.com')).resolve(),
        log_dir=Path(os.getenv('LOG_DIR', root / 'logs')).resolve(),
        openai_api_key=os.getenv('OPENAI_API_KEY', ''),
        openai_base_url=os.getenv('OPENAI_BASE_URL', 'https://ai.dooo.ng/v1/chat/completions'),
        openai_model=os.getenv('OPENAI_MODEL', 'gpt-5.4'),
    )
