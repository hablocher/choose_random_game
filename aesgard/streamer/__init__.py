# -*- coding: utf-8 -*-
"""
Streamer & Live Broadcasting package for Canino Gaming.
Provides OBS overlays, interactive chat bots, Twitch polls, bingo, challenges, and stream cards.
"""

from .live_history import LiveHistoryManager
from .overlay_window import StreamerOverlayWindow
from aesgard.web_overlay import (
    start_overlay_server,
    update_overlay_game,
    update_overlay_timer,
    update_overlay_channel,
    update_overlay_poll,
    record_poll_vote,
)
from aesgard.card_generator import generate_live_card
from aesgard.chat_bot import get_chat_bot, TwitchChatBot
from aesgard.bingo import LiveBingoDialog
from aesgard.challenges import (
    get_random_challenge,
    set_active_challenge,
    get_active_challenge,
    clear_challenge,
)
from aesgard.vibe import (
    classify_game_vibe,
    filter_games_by_vibe,
    generate_curator_pitch,
)

__all__ = [
    "LiveHistoryManager",
    "StreamerOverlayWindow",
    "start_overlay_server",
    "update_overlay_game",
    "update_overlay_timer",
    "update_overlay_channel",
    "update_overlay_poll",
    "record_poll_vote",
    "generate_live_card",
    "get_chat_bot",
    "TwitchChatBot",
    "LiveBingoDialog",
    "get_random_challenge",
    "set_active_challenge",
    "get_active_challenge",
    "clear_challenge",
    "classify_game_vibe",
    "filter_games_by_vibe",
    "generate_curator_pitch",
]
