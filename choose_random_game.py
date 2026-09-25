# -*- coding: utf-8 -*-
"""
Canino Gaming - Ponto de Entrada Principal.
Inspirado na obra Caninos Brancos (White Fang) de Jack London.
Agrega jogos de pastas locais, atalhos, eXoDOS (instalados) e Playnite.
Inicia o Painel Selvagem do Canino Gaming.
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
logger = logging.getLogger("canino_gaming")

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
        
    # 2. Query Playnite Library (Unifies Steam, GOG, Epic, Emulators, etc.)
    playniteEntries = []
    playniteEntriesWithStatus = []
    if getattr(config, 'playniteEnabled', True):
        try:
            playnite_path = config.playnitePath or getDefaultPlaynitePath()
            playnite_games = loadPlayniteGames(
                playnitePath=playnite_path,
                onlyInstalled=config.playniteOnlyInstalled,
                exportJsonPath=config.playniteExportJson
            )
            playniteEntriesWithStatus = formatPlayniteEntries(playnite_games, includeInstalledFlag=True)
            playniteEntries = [entry for entry, _ in playniteEntriesWithStatus]
            logger.info(f"Loaded {len(playniteEntries)} games from Playnite (onlyInstalled={config.playniteOnlyInstalled}).")
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
        
    # 6. Batch import games to database with accurate installation status
    if config.importContentToDatabase:
        if playniteEntriesWithStatus:
            import_items = list(playniteEntriesWithStatus)
            known_playnite = {entry for entry, _ in playniteEntriesWithStatus}
            for c in content:
                if c not in known_playnite:
                    import_items.append((c, 1))
            importContentToDatabase(import_items)
        else:
            importContentToDatabase(content)

    # 7. Initial random selection
    choosedGame = chooseGame(content, sampleSize=config.randomSampleSize)
        
    print("==================================================")
    print(f"🐺 CANINO GAMING • {len(content)} presas no território!")
    print(f"PRESA ESCOLHIDA ----------> {choosedGame} <----------")
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
