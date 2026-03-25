from __future__ import annotations

from .config import load_settings
from .logging_utils import get_logger
from .models import RunResult


def run() -> RunResult:
    settings = load_settings()
    logger = get_logger(settings.log_dir)
    logger.info('application skeleton initialized')
    return RunResult(
        ok=True,
        stage='bootstrap',
        message='night_journal application skeleton ready',
        data={
            'engine_root': str(settings.engine_root),
            'automation_dir': str(settings.automation_dir),
            'output_dir': str(settings.output_dir),
            'model': settings.openai_model,
        },
    )
