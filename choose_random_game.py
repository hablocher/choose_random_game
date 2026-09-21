# -*- coding: utf-8 -*-
"""
Choose Random Game - Main Entry Point.
Aggregates games from Local folders, Shortcuts, eXoDOS (installed only), and Playnite.
Launches the Modern Gaming Dashboard.
"""
import sys
import logging

from aesgard.playnite import loadPlayniteGames, formatPlayniteEntries, getDefaultPlaynitePath
from aesgard.gameutil import prepareContent, preparelinksList, chooseGame
from aesgard.util import writeListToFile, LogException
from aesgard.database import init as databaseInit, importContentToDatabase, syncGotyGames
from aesgard.ui import showChoosedGame
from aesgard.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("choose_random_game")

def run(argv):
    config = Config()
    config.read_config(argv)
    
    # 1. Initialize Database
    try:
        databaseInit(
            config.DatabaseServer, 
            config.DatabaseUser, 
            config.DatabasePassword, 
            config.DatabaseName, 
            config.DatabaseType,
            table_name=config.DatabaseTableName
        )
    except Exception as e:
        LogException("Error initializing database!", e)
        return
        
    # 2. Query Playnite Library (Unifies Steam, GOG, Epic, etc.)
    playniteEntries = []
    if getattr(config, 'playniteEnabled', True):
        try:
            playnite_path = config.playnitePath or getDefaultPlaynitePath()
            playnite_games = loadPlayniteGames(
                playnitePath=playnite_path,
                onlyInstalled=config.playniteOnlyInstalled,
                exportJsonPath=config.playniteExportJson
            )
            playniteEntries = formatPlayniteEntries(playnite_games)
            logger.info(f"Loaded {len(playniteEntries)} installed games from Playnite.")
        except Exception as e:
            logger.warning(f"Error loading Playnite games: {e}")

    # 3. Parse Local Shortcuts (.lnk, .url and Desktop)
    linksList = preparelinksList(
        config.foldersWithLinks, 
        config.baseLinks,
        includeDesktop=config.includeDesktop,
        desktopPath=config.desktopPath
    )
    
    # 4. Aggregate ALL active sources: Local folders + eXoDOS (installed only) + Shortcuts + Playnite
    content = list(set(
        prepareContent(
            config.gameFolders, 
            config.gameCommonFolders, 
            linksList,
            config.removals,
            config.endswith,
            exodosLocation=config.EXODOSLocation,
            playniteEntries=playniteEntries,
            metadataFolder=config.EXODOSMetadataFolder,
            onlyInstalled=config.EXODOSOnlyInstalled
        )
    ))

    if not content:
        print("No games found! Please check your choose_random_game.ini configuration.")
        return

    # 5. Write debug lists to disk if configured
    if config.createFiles:
        writeListToFile(config.pathToSave + config.gamesFoundFileName, content)
        
    # 6. Batch import games to database
    if config.importContentToDatabase:
        importContentToDatabase(content)

    # 7. Initial random selection
    choosedGame = chooseGame(content, sampleSize=config.randomSampleSize)
        
    print("==================================================")
    print(f"You have {len(content)} games to play!")
    print(f"CHOSEN GAME -----------> {choosedGame} <-----------")
    print("==================================================")

    # 8. Sync GOTY collection with user's library
    try:
        syncGotyGames(content)
    except Exception as e:
        logger.warning(f"Error syncing GOTY database: {e}")

    # 9. Display Modern Gaming Dashboard (with fallback to Tkinter if needed)
    try:
        from aesgard.dashboard import showDashboard
        showDashboard(choosedGame, [], content, config)
    except Exception as e:
        logger.warning(f"Could not start PyQt6 Dashboard, using fallback UI: {e}")
        showChoosedGame(choosedGame, [], content=content)

if __name__ == '__main__':
    run(sys.argv)
