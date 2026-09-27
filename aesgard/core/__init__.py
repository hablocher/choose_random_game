# -*- coding: utf-8 -*-
"""
Core business logic, configuration, utilities, and database management for Canino Gaming.
"""

from aesgard.config import Config
from aesgard.database import (
    init as databaseInit,
    getDatabaseStats,
    getGamesList,
    setFinished,
    setFavorite,
    findGameInfo,
    importContentToDatabase,
    getInstalledGamesSet,
    getUninstalledGamesSet,
    getFavoriteGamesSet,
    getPlayedGamesSet,
)
from aesgard.gameutil import (
    executeGame,
    installGame,
    scanAllSources,
    findGameIcon,
    chooseGame,
    getGameOfTheDay,
    prepareContent,
    preparelinksList,
)
from aesgard.util import writeListToFile, LogException
from aesgard.backup import backup_game_saves

__all__ = [
    "Config",
    "databaseInit",
    "getDatabaseStats",
    "getGamesList",
    "setFinished",
    "setFavorite",
    "findGameInfo",
    "importContentToDatabase",
    "getInstalledGamesSet",
    "getUninstalledGamesSet",
    "getFavoriteGamesSet",
    "getPlayedGamesSet",
    "executeGame",
    "installGame",
    "scanAllSources",
    "findGameIcon",
    "chooseGame",
    "getGameOfTheDay",
    "prepareContent",
    "preparelinksList",
    "writeListToFile",
    "LogException",
    "backup_game_saves",
]
