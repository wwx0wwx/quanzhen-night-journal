"""Seed memories for the default persona.

Delegates to the preset loader.  Kept as a separate module for backward
compatibility with existing imports.
"""

from __future__ import annotations

from backend.utils.default_persona import get_preset_memories


def get_seed_memories(persona_id: int) -> list[dict]:
    """Return seed memories bound to *persona_id*, ready for batch insert."""
    return get_preset_memories(persona_id)
