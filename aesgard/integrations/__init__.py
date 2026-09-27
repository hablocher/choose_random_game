# -*- coding: utf-8 -*-
"""
Integrations with external libraries and platforms (Playnite, Steam, GOG, GOTY, HLTB, Covers).
"""

from aesgard.playnite import (
    loadPlayniteGames,
    formatPlayniteEntries,
    getDefaultPlaynitePath,
    PLAYNITE_PREFIX,
)
from aesgard.steam import (
    cleanSteamTitle,
    fetchSteamCover,
    findLocalSteamGridCover,
    launchSteamGame,
    DEFAULT_STEAM_PATH,
)
from aesgard.gog import (
    cleanGOGTitle,
    fetchGOGCover,
    findGOGGameFolderCover,
    getGOGGalaxyGames,
    launchGOGGame,
)
from aesgard.goty import (
    initGotyDatabase,
    getRandomGoty,
    getAllGotys,
    isGotyInstalledInLibrary,
)
from aesgard.hltb import (
    get_cached_hltb,
    fetch_hltb_data,
    format_hltb_duration,
    get_duration_badge_style,
    clean_title_for_hltb,
    get_all_cached_durations,
    preload_hltb_cache,
)
from aesgard.covers import (
    resolveGameCover,
    fetchFromSteamStore,
    fetchFromWikipedia,
    getDefaultCover,
    generateProceduralCover,
)
from aesgard.game_intel import (
    getGuideLinks,
    findLocalGameManuals,
    fetchGameSynopsis,
    getFullGameIntel,
)

__all__ = [
    "loadPlayniteGames",
    "formatPlayniteEntries",
    "getDefaultPlaynitePath",
    "PLAYNITE_PREFIX",
    "cleanSteamTitle",
    "fetchSteamCover",
    "findLocalSteamGridCover",
    "launchSteamGame",
    "DEFAULT_STEAM_PATH",
    "cleanGOGTitle",
    "fetchGOGCover",
    "findGOGGameFolderCover",
    "getGOGGalaxyGames",
    "launchGOGGame",
    "initGotyDatabase",
    "getRandomGoty",
    "getAllGotys",
    "isGotyInstalledInLibrary",
    "get_cached_hltb",
    "fetch_hltb_data",
    "format_hltb_duration",
    "get_duration_badge_style",
    "clean_title_for_hltb",
    "get_all_cached_durations",
    "preload_hltb_cache",
    "resolveGameCover",
    "fetchFromSteamStore",
    "fetchFromWikipedia",
    "getDefaultCover",
    "generateProceduralCover",
    "getGuideLinks",
    "findLocalGameManuals",
    "fetchGameSynopsis",
    "getFullGameIntel",
]
