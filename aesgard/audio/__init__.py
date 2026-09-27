# -*- coding: utf-8 -*-
"""
Audio & Sound Effects (SFX) Engine for Canino Gaming.
"""

from .sound import (
    SoundManager,
    get_sound_manager,
    generate_synthesized_sounds,
    generate_thematic_sounds,
)

__all__ = [
    "SoundManager",
    "get_sound_manager",
    "generate_synthesized_sounds",
    "generate_thematic_sounds",
]
