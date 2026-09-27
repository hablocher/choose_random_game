# -*- coding: utf-8 -*-
"""
User Interface (UI) package for Canino Gaming.
Exports formatting utilities, design tokens, stylesheets, themes, views, and dialogs.
"""

from .formatting import (
    formatDisplayName,
    detectPlatform,
    getPlatformColor,
    clearPlayniteMetaCache,
)
from .styles import STYLESHEET
from .theme import ThemedCentralWidget, extractChannelHandle, BACKGROUND_PRESETS
from .legacy_ui import GameChooserUI, showChoosedGame

__all__ = [
    "formatDisplayName",
    "detectPlatform",
    "getPlatformColor",
    "clearPlayniteMetaCache",
    "STYLESHEET",
    "ThemedCentralWidget",
    "extractChannelHandle",
    "BACKGROUND_PRESETS",
    "GameChooserUI",
    "showChoosedGame",
]
