from __future__ import annotations

import inspect

from backend.engine.context_builder import ContextBuilder
from backend.engine.folder_monitor_manager import FolderMonitorManager
from backend.engine.runtime_factory import build_generation_runtime
from backend.scheduler import jobs


def test_folder_monitor_source_uses_runtime_factory():
    src = inspect.getsource(FolderMonitorManager.process_file)
    assert "build_generation_runtime" in src
    assert "config_store" in inspect.getsource(ContextBuilder.__init__)


def test_jobs_runtime_uses_factory():
    src = inspect.getsource(jobs._runtime)
    assert "build_generation_runtime" in src


def test_factory_exports_orchestrator_tuple():
    assert callable(build_generation_runtime)
