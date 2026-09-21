# -*- coding: utf-8 -*-
"""
Game utility module for Choose Random Game.
Handles folder parsing, executable matching, icon extraction, and game launching.
Fully supports:
- Local game installations and directories
- Windows shortcuts (.lnk, .url) and Desktop games
- eXoDOS installed collection (only games actually downloaded in G:/eXoDOS_Lite/eXo/eXoDOS)
- DOSBox standalone games
- Playnite catalog (which unifies Steam, GOG, Epic, etc.)
"""
import random
import jellyfish
import os
import sys
import logging
import win32com.client 
import requests

from PIL import Image
from io import BytesIO

from aesgard.playnite import launchPlayniteGame, getPlayniteCoverPath, PLAYNITE_PREFIX
from aesgard.database import insertGameInfo, findGameInfo
from aesgard.winicon import extract_icon, IconSize
from aesgard.util import win32_icon_to_image, LogException
from aesgard.config import Config

logger = logging.getLogger(__name__)

__CONFIG__ = Config()
__CONFIG__.read_config(sys.argv)

linkPrefix = getattr(__CONFIG__, 'linkPrefix', 'link::')
exodosPrefix = getattr(__CONFIG__, 'exodosPrefix', 'exodos:')

def normalizeString(text):
    """Normalizes string for comparison by removing spaces and symbols."""
    chars_to_remove = [" ", ":", "-", "'", '"', ",", "!", "+", "(", ")", ".", "_"]
    result = text.lower()
    for c in chars_to_remove:
        result = result.replace(c, "")
    return result

def checkExeFile(launch, choosed, maxDist=None, jwThreshold=None):
    """
    Checks if an executable matches the chosen game folder name.
    Uses configurable Levenshtein distance and Jaro-Winkler similarity thresholds.
    """
    maxDist = maxDist if maxDist is not None else getattr(__CONFIG__, 'levenshteinMaxDistance', 2)
    jwThreshold = jwThreshold if jwThreshold is not None else getattr(__CONFIG__, 'jaroWinklerThreshold', 0.85)

    launch_clean = normalizeString(launch.replace('.exe', ''))
    choosed_clean = normalizeString(choosed)

    if launch.lower() == 'launcher.exe':
        return True

    dist = jellyfish.levenshtein_distance(launch_clean, choosed_clean)
    if dist <= maxDist:
        return True

    if len(launch_clean) >= 4 and (launch_clean in choosed_clean or choosed_clean in launch_clean):
        return True

    if jellyfish.jaro_winkler_similarity(launch_clean, choosed_clean) >= jwThreshold:
        return True

    return False    

def findLauncher(choosedGame, launcherPrefixes, shortcutExt):
    """Finds a designated launcher shortcut or executable inside the game folder."""
    if os.path.isdir(choosedGame):
        try:
            for launch in next(os.walk(choosedGame))[2]:
                for key, prefix in launcherPrefixes:
                    if launch.lower().startswith(prefix.lower()) and launch.lower().endswith(shortcutExt.lower()): 
                        return launch
        except StopIteration:
            pass
    return None

def findLauncherAndStart(choosedGame, launcherPrefixes, shortcutExt):
    """Searches for launcher and launches it if found."""
    launch = findLauncher(choosedGame, launcherPrefixes, shortcutExt)
    if launch is not None:
        logger.info(f"Calling launcher '{launch}' in '{choosedGame}'")
        os.chdir(choosedGame)
        os.startfile(launch)
        return True
    return False

def findClientURL(choosedGame, otherClients, shortcutExt):
    """Resolves URL or shortcut (.lnk) files."""
    if choosedGame.startswith(linkPrefix):
        launch = choosedGame[len(linkPrefix):]
        if launch.lower().endswith(shortcutExt.lower()) or launch.lower().endswith(".url"):
            return launch
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            linkFile = launch + shortcutExt
            if os.path.exists(linkFile):
                shortcut = shell.CreateShortcut(linkFile)
                for key, client in otherClients:
                    if shortcut.Targetpath.startswith(client):
                        return shortcut.Targetpath
                return shortcut.Targetpath
                
            linkFile = launch + ".url"
            if os.path.exists(linkFile):
                shortcut = shell.CreateShortcut(linkFile)
                for key, client in otherClients:
                    if shortcut.Targetpath.startswith(client):
                        return shortcut.Targetpath
                return shortcut.Targetpath
        except Exception as e:
            logger.warning(f"Error resolving shortcut '{launch}': {e}")
    return None

def startLink(choosedGame, otherClients, shortcutExt):
    """Starts game from link if it is a shortcut."""
    url = findClientURL(choosedGame, otherClients, shortcutExt)
    if url is not None:
        logger.info(f"Opening link: {url}")
        os.startfile(url)
        return True
    return False

def openDOSBOX(choosedGame, DOSBOXLocation, DOSBOXExecutable, DOSBOXParameters):
    """Launches a DOSBox game."""
    if "dosbox" in choosedGame.lower():
        logger.info(f"Executing DOSBOX Game '{choosedGame}'")
        posLastBar = choosedGame.rfind("/") + 1
        game_folder_name = choosedGame[posLastBar:]
        params = DOSBOXParameters.format(f'"cd {game_folder_name}"')
        if os.path.isdir(DOSBOXLocation):
            os.chdir(DOSBOXLocation)
            os.system(f"{DOSBOXExecutable} {params}")
            return True
    return False

def geteXoDOSGameDetails(gamePath, installBat=None):
    """Finds the main .bat launcher and full title for an eXoDOS game."""
    if not os.path.isdir(gamePath):
        return None, os.path.basename(gamePath)
    
    installBat = (installBat or getattr(__CONFIG__, 'EXODOSInstallBat', 'install.bat')).lower()
    try:
        files = os.listdir(gamePath)
        for f in files:
            if f.lower().endswith('.bat') and f.lower() != installBat:
                clean_name = os.path.splitext(f)[0]
                return f, clean_name
    except Exception:
        pass
    return None, os.path.basename(gamePath)

def findeXoDOSGame(choosedGame, EXODOSLocation, metadataFolder=None, installBat=None):
    """Launches an eXoDOS game bat file."""
    if choosedGame.startswith(exodosPrefix) or "exodos" in choosedGame.lower():
        target_dir = choosedGame[len(exodosPrefix):] if choosedGame.startswith(exodosPrefix) else choosedGame
        folder_name = os.path.basename(target_dir.rstrip("/\\"))
        metadataFolder = metadataFolder or getattr(__CONFIG__, 'EXODOSMetadataFolder', '!dos')

        # Look for the launcher bat in <metadataFolder>/<folder_name> first (standard eXoDOS launcher location)
        dos_bat_dir = os.path.join(EXODOSLocation, metadataFolder, folder_name)
        candidates = [dos_bat_dir, target_dir]
        for c in candidates:
            if os.path.isdir(c):
                bat_file, title = geteXoDOSGameDetails(c, installBat=installBat)
                if bat_file:
                    logger.info(f"Executing eXoDOS Game '{bat_file}' in '{c}'")
                    os.chdir(c)
                    os.startfile(bat_file)
                    return True
    return False

def findEXE(choosedGame):
    """Finds the main executable inside a game folder."""
    if not os.path.isdir(choosedGame):
        return None
        
    posLastBar = choosedGame.rfind("/")
    folder_name = choosedGame[posLastBar:]
    exeCount = 0
    exeFolder = choosedGame
    exeFile = ""

    try:
        files = next(os.walk(choosedGame))[2]
    except StopIteration:
        return None

    for launch in files:
        if launch.lower().endswith('.exe'):
            exeCount += 1
            exeFile = launch
            if checkExeFile(exeFile.lower(), folder_name.lower()):
                logger.info(f"Matched EXE '{launch}' in '{choosedGame}'")
                return (exeFile, exeFolder)
                
    if exeCount == 1 and 'uninst' not in exeFile.lower():
        logger.info(f"Single EXE found: '{exeFile}'")
        return (exeFile, exeFolder)

    return None

def executeEXE(choosedGame):
    """Executes matched EXE if available."""
    exeInfo = findEXE(choosedGame)
    if exeInfo is not None:
        os.chdir(exeInfo[1])
        os.startfile(exeInfo[0])
        return True
    return False

def fallBackToGameFolder(choosedGame):
    """Opens folder in explorer if no direct launcher was found."""
    clean = choosedGame
    if clean.startswith(exodosPrefix):
        clean = clean[len(exodosPrefix):]
    elif clean.startswith(linkPrefix):
        clean = os.path.dirname(clean[len(linkPrefix):])
        
    if os.path.isdir(clean):
        logger.info(f"Opening game folder: '{clean}'")
        os.startfile(clean)
        return True
    return False

import datetime

def getGameOfTheDay(content, seed_date=True):
    """
    Selects a Game of the Day, prioritizing installed games if available in the database.
    When seed_date is True, the selection remains consistent for the entire calendar day.
    """
    if not content:
        return ""
    
    # Prioritize installed games if known
    installed_candidates = []
    for g in content:
        info = findGameInfo(g)
        if info and len(info) >= 7:
            if info[6] == 1:
                installed_candidates.append(g)
        else:
            installed_candidates.append(g)
            
    pool = installed_candidates if installed_candidates else content
    if seed_date:
        today_str = datetime.date.today().isoformat()
        idx = abs(hash(today_str)) % len(pool)
        return pool[idx]
    return random.choice(pool)

def extractWin32GameIcon(choosedGame, targetSize=(160, 160)):
    """Extracts Windows icon from shortcut (.lnk) or executable (.exe) as fallback."""
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        
        # Shortcut Link
        if choosedGame.startswith(linkPrefix):
            link_path = choosedGame[len(linkPrefix):]
            if os.path.exists(link_path):
                if link_path.lower().endswith(getattr(__CONFIG__, 'shortcutExt', '.lnk').lower()):
                    try:
                        shortcut = shell.CreateShortcut(link_path)
                        target = shortcut.Targetpath
                        if os.path.exists(target):
                            icon = extract_icon(target, IconSize.LARGE)
                            if icon:
                                return win32_icon_to_image(icon, IconSize.LARGE).resize(targetSize)
                    except Exception:
                        pass
                icon = extract_icon(link_path, IconSize.LARGE)
                if icon:
                    return win32_icon_to_image(icon, IconSize.LARGE).resize(targetSize)

        launch = findLauncher(choosedGame, __CONFIG__.launcherPrefixes, __CONFIG__.shortcutExt)
        if launch is not None:
            try:
                shortcut = shell.CreateShortcut(os.path.join(choosedGame, launch))
                if os.path.exists(shortcut.Targetpath):
                    icon = extract_icon(shortcut.Targetpath, IconSize.LARGE)
                    if icon:
                        return win32_icon_to_image(icon, IconSize.LARGE).resize(targetSize)
            except Exception:
                pass
                
        exeFile = findEXE(choosedGame)
        if exeFile is not None:
            full_exe = os.path.join(exeFile[1], exeFile[0])
            if os.path.exists(full_exe):
                icon = extract_icon(full_exe, IconSize.LARGE)
                if icon:
                    return win32_icon_to_image(icon, IconSize.LARGE).resize(targetSize)
    except Exception as e:
        logger.debug(f"Could not extract Windows icon: {e}")

    return None

def findGameIcon(*args, **kwargs):
    """
    Retrieves or generates an image/cover for the chosen game using the complete
    multi-tier strategy:
    1. Local disk cache (covers_cache/)
    2. Playnite database & media storage (library/files)
    3. Steam Storefront Database (Public API with automatic caching)
    4. Specialized databases (eXoDOS Extras, Wikipedia)
    5. Executable (.exe) or Shortcut (.lnk) embedded icon extraction via Win32 API
    6. Procedural High-Quality Gamer Card Generator (Guaranteed Fallback)
    """
    choosedGame = ""
    playnitePath = kwargs.get("playnitePath", "")
    cover_size = kwargs.get("coverSize", None)

    if len(args) == 1:
        choosedGame = args[0]
    elif len(args) >= 3 and isinstance(args[0], (list, tuple, type(None))):
        choosedGame = args[2]
        if len(args) >= 4:
            playnitePath = args[3]
    elif len(args) >= 1 and isinstance(args[0], str):
        choosedGame = args[0]
        if len(args) >= 2 and isinstance(args[1], str):
            playnitePath = args[1]

    if cover_size is None:
        cover_w = getattr(__CONFIG__, 'uiCoverWidth', 160)
        cover_h = getattr(__CONFIG__, 'uiCoverHeight', 160)
        cover_size = (cover_w, cover_h)

    from aesgard.covers import resolveGameCover

    return resolveGameCover(
        choosedGame,
        config=__CONFIG__,
        targetSize=cover_size,
        win32_extractor=extractWin32GameIcon
    )


def preparelinksList(foldersWithLinks, baseLinks, includeDesktop=None, desktopPath=None):
    """
    Parses folders containing game shortcuts recursively (.lnk and .url),
    plus desktop shortcuts if configured.
    """
    linksList = []
    allowed_exts = ('.lnk', '.url')
    
    includeDesktop = includeDesktop if includeDesktop is not None else getattr(__CONFIG__, 'includeDesktop', True)
    desktopPath = desktopPath or getattr(__CONFIG__, 'desktopPath', os.path.join(os.path.expanduser("~"), "Desktop"))

    # 1. Configured shortcut folders
    for key, link in foldersWithLinks:
        target_dir = os.path.join(baseLinks, link) if (baseLinks and os.path.isdir(os.path.join(baseLinks, link))) else link
        if os.path.isdir(target_dir):
            for root, _, files in os.walk(target_dir):
                for f in files:
                    if f.lower().endswith(allowed_exts):
                        full_p = os.path.join(root, f).replace("\\", "/")
                        linksList.append(f"{linkPrefix}{full_p}")

    # 2. Desktop shortcuts (if enabled)
    if includeDesktop and os.path.isdir(desktopPath):
        for f in os.listdir(desktopPath):
            if f.lower().endswith(allowed_exts):
                full_p = os.path.join(desktopPath, f).replace("\\", "/")
                linksList.append(f"{linkPrefix}{full_p}")

    return list(set(linksList))

def prepareExoDOSGames(exodosLocation, metadataFolder=None, onlyInstalled=None):
    """
    Scans eXoDOS for installed games.
    If onlyInstalled is True, subfolders in exodosLocation (excluding metadataFolder) are returned.
    """
    games = []
    if not exodosLocation or not os.path.isdir(exodosLocation):
        return games

    metadataFolder = (metadataFolder or getattr(__CONFIG__, 'EXODOSMetadataFolder', '!dos')).lstrip('/\\')
    onlyInstalled = onlyInstalled if onlyInstalled is not None else getattr(__CONFIG__, 'EXODOSOnlyInstalled', True)

    try:
        if onlyInstalled:
            subdirs = next(os.walk(exodosLocation))[1]
            for folder in subdirs:
                # Ignore metadata folders
                if folder.startswith("!") or folder.lower() == metadataFolder.lower():
                    continue
                full_path = os.path.join(exodosLocation, folder).replace("\\", "/")
                games.append(f"{exodosPrefix}{full_path}")
            logger.info(f"Loaded {len(games)} INSTALLED games from eXoDOS ({exodosLocation})")
        else:
            dos_dir = os.path.join(exodosLocation, metadataFolder)
            search_dir = dos_dir if os.path.isdir(dos_dir) else exodosLocation
            subdirs = next(os.walk(search_dir))[1]
            for folder in subdirs:
                if folder.startswith("!"):
                    continue
                full_path = os.path.join(search_dir, folder).replace("\\", "/")
                games.append(f"{exodosPrefix}{full_path}")
            logger.info(f"Loaded {len(games)} games from eXoDOS catalog ({search_dir})")
    except Exception as e:
        logger.warning(f"Error scanning eXoDOS games: {e}")

    return games

def prepareContent(gameFolders, 
                   gameCommonFolders, 
                   linksList, 
                   removals,
                   endswith,
                   exodosLocation=None,
                   playniteEntries=None,
                   metadataFolder=None,
                   onlyInstalled=None):
    """
    Gathers game entries from all active sources:
    - Local game folders (e.g. D:/Jogos, E:/Jogos, DOSBox)
    - Common subfolders
    - eXoDOS installed games only
    - Local shortcut links (.lnk, .url and Desktop)
    - Playnite library (which manages Steam, GOG, Epic, etc.)
    """
    content = []
    ends = tuple(t[1].lower() for t in endswith) if endswith else ()

    # 1. Local game folders
    for key, gameFolder in gameFolders:
        if exodosLocation and os.path.abspath(str(gameFolder)) == os.path.abspath(str(exodosLocation)):
            continue

        if gameCommonFolders:
            for key_c, common in gameCommonFolders:
                folder = os.path.join(str(gameFolder), str(common).strip("/\\"))
                if os.path.isdir(folder):
                    try:
                        for game in next(os.walk(folder))[1]:
                            g = os.path.join(folder, game).lower().replace("\\", "/")
                            if not g.endswith(ends):
                                content.append(g)
                    except StopIteration:
                        pass
        else:
            if os.path.isdir(gameFolder):
                try:
                    for game in next(os.walk(gameFolder))[1]:
                        g = os.path.join(gameFolder, game).lower().replace("\\", "/")
                        if not g.endswith(ends):
                            content.append(g)
                except StopIteration:
                    pass

    # 2. eXoDOS Games
    if exodosLocation:
        exodos_games = prepareExoDOSGames(
            exodosLocation,
            metadataFolder=metadataFolder,
            onlyInstalled=onlyInstalled
        )
        content.extend(exodos_games)

    # 3. Links / Shortcuts (including Desktop)
    for link in linksList:
        content.append(link)

    # 4. Playnite Entries (unifies Steam, GOG, Epic, etc.)
    if playniteEntries:
        content.extend(playniteEntries)

    # 5. Apply Removals / Filters
    for key, removal in removals:
        content = [g if g.startswith(exodosPrefix) else g.replace(removal, '') for g in content]
        
    content = list(filter(None, content))
    return list(set(content))

def executeGame(choosedGame, steamOwnedGames=None):
    """
    Executes the chosen game using the appropriate strategy.
    Updates the database with play count and last played date.
    """
    try:
        insertGameInfo(choosedGame)

        # 1. Playnite Game
        if choosedGame.startswith(PLAYNITE_PREFIX):
            parts = choosedGame.split(":")
            game_id = parts[-1]
            uriPrefix = getattr(__CONFIG__, 'playniteUriPrefix', 'playnite://playnite/start/')
            if launchPlayniteGame(game_id, uriPrefix=uriPrefix):
                return True

        # 2. eXoDOS Game
        if choosedGame.startswith(exodosPrefix) or "exodos" in choosedGame.lower():
            if findeXoDOSGame(
                choosedGame, 
                __CONFIG__.EXODOSLocation, 
                metadataFolder=getattr(__CONFIG__, 'EXODOSMetadataFolder', '!dos'),
                installBat=getattr(__CONFIG__, 'EXODOSInstallBat', 'install.bat')
            ):
                return True

        # 3. Shortcut Link (.lnk, .url)
        if choosedGame.startswith(linkPrefix) or startLink(choosedGame, __CONFIG__.otherClients, __CONFIG__.shortcutExt):
            target = findClientURL(choosedGame, __CONFIG__.otherClients, __CONFIG__.shortcutExt)
            if target:
                os.startfile(target)
                return True

        # 4. Launcher inside folder
        if findLauncherAndStart(choosedGame, __CONFIG__.launcherPrefixes, __CONFIG__.shortcutExt):
            return True

        # 5. DOSBox Game
        if openDOSBOX(choosedGame, __CONFIG__.DOSBOXLocation, __CONFIG__.DOSBOXExecutable, __CONFIG__.DOSBOXParameters):
            return True

        # 6. Executable Match
        if executeEXE(choosedGame):
            return True

        # 7. Fallback to opening folder
        if fallBackToGameFolder(choosedGame):
            return True

    except Exception as e:
        logger.error(f"Failed to start '{choosedGame}': {e}")
        return False
        
    return False

def installGame(choosedGame):
    """
    Triggers installation or download for an uninstalled game based on source:
    - Playnite: via playnite://playnite/install/<id>
    - Steam: via steam://install/<app_id>
    - eXoDOS: executes install.bat or setup
    - Local / Shortcut: opens target folder in Explorer
    """
    try:
        # 1. Playnite Game
        if choosedGame.startswith(PLAYNITE_PREFIX):
            parts = choosedGame.split(":")
            game_id = parts[-1]
            from aesgard.playnite import installPlayniteGame
            return installPlayniteGame(game_id)

        # 2. Direct Steam AppID
        if choosedGame.startswith("steam:"):
            app_id = choosedGame.split(":")[-1]
            os.startfile(f"steam://install/{app_id}")
            return True

        # 3. eXoDOS Game
        if choosedGame.startswith(exodosPrefix) or "exodos" in choosedGame.lower():
            target_dir = choosedGame[len(exodosPrefix):] if choosedGame.startswith(exodosPrefix) else choosedGame
            folder_name = os.path.basename(target_dir.rstrip("/\\"))
            metadataFolder = getattr(__CONFIG__, 'EXODOSMetadataFolder', '!dos')
            dos_bat_dir = os.path.join(getattr(__CONFIG__, 'EXODOSLocation', '') or '', metadataFolder, folder_name)
            for c in [target_dir, dos_bat_dir]:
                if os.path.isdir(c):
                    install_bat = os.path.join(c, "install.bat")
                    if os.path.exists(install_bat):
                        os.chdir(c)
                        os.startfile(install_bat)
                        return True
                    for f in os.listdir(c):
                        if f.lower().endswith('.bat') and 'install' in f.lower():
                            os.chdir(c)
                            os.startfile(os.path.join(c, f))
                            return True

        # 4. Local folder or shortcut fallback: open in Explorer
        clean_path = choosedGame
        if clean_path.startswith(linkPrefix):
            clean_path = clean_path[len(linkPrefix):]
        if os.path.exists(clean_path):
            os.startfile(clean_path if os.path.isdir(clean_path) else os.path.dirname(clean_path))
            return True

    except Exception as e:
        logger.error(f"Failed to install '{choosedGame}': {e}")
        return False

    return False

def scanAllSources(config=None, includeUninstalled=True):
    """
    Scans all configured sources and returns a deduplicated list of (gameEntry, is_installed) tuples.
    Includes Playnite (installed and uninstalled), local folders, shortcuts, and eXoDOS.
    """
    cfg = config or __CONFIG__
    results = []

    # 1. Playnite Catalog
    if getattr(cfg, 'enablePlaynite', True):
        try:
            from aesgard.playnite import loadPlayniteGames, formatPlayniteEntries
            playnite_path = getattr(cfg, 'playnitePath', None) or getattr(cfg, 'playniteDatabasePath', None)
            playnite_games = loadPlayniteGames(
                playnite_path,
                onlyInstalled=(not includeUninstalled),
                exportJsonPath=getattr(cfg, 'playniteExportJson', None)
            )
            entries_with_status = formatPlayniteEntries(playnite_games, includeInstalledFlag=True)
            results.extend(entries_with_status)
        except Exception as e:
            logger.warning(f"Error scanning Playnite games in scanAllSources: {e}")

    # 2. Local game folders
    ends = tuple(t[1].lower() for t in getattr(cfg, 'endswith', [])) if getattr(cfg, 'endswith', None) else ()
    exodosLocation = getattr(cfg, 'EXODOSLocation', None)
    
    local_candidates = []
    gameFolders = getattr(cfg, 'gameFolders', [])
    gameCommonFolders = getattr(cfg, 'gameCommonFolders', [])
    
    for key, gameFolder in gameFolders:
        if exodosLocation and os.path.abspath(str(gameFolder)) == os.path.abspath(str(exodosLocation)):
            continue
        if gameCommonFolders:
            for key_c, common in gameCommonFolders:
                folder = os.path.join(str(gameFolder), str(common).strip("/\\"))
                if os.path.isdir(folder):
                    try:
                        for game in next(os.walk(folder))[1]:
                            g = os.path.join(folder, game).lower().replace("\\", "/")
                            if not g.endswith(ends):
                                local_candidates.append(g)
                    except StopIteration:
                        pass
        else:
            if os.path.isdir(gameFolder):
                try:
                    for game in next(os.walk(gameFolder))[1]:
                        g = os.path.join(gameFolder, game).lower().replace("\\", "/")
                        if not g.endswith(ends):
                            local_candidates.append(g)
                except StopIteration:
                    pass

    removals = getattr(cfg, 'removals', [])
    for cand in set(local_candidates):
        clean_g = cand
        for key, removal in removals:
            clean_g = clean_g.replace(removal, '')
        if clean_g:
            is_inst, _, _ = isGameInstalledOnSystem(clean_g, cfg)
            results.append((clean_g, 1 if is_inst else 0))

    # 3. Shortcuts / Desktop
    linksList = preparelinksList(
        getattr(cfg, 'foldersWithLinks', []),
        getattr(cfg, 'baseLinks', None),
        includeDesktop=getattr(cfg, 'includeDesktop', True),
        desktopPath=getattr(cfg, 'desktopPath', None)
    )
    for link in set(linksList):
        clean_link = link
        for key, removal in removals:
            clean_link = clean_link.replace(removal, '')
        if clean_link:
            is_inst, _, _ = isGameInstalledOnSystem(clean_link, cfg)
            results.append((clean_link, 1 if is_inst else 0))

    # 4. eXoDOS Games
    if exodosLocation and os.path.isdir(exodosLocation):
        metadataFolder = getattr(cfg, 'EXODOSMetadataFolder', '!dos').lstrip('/\\')
        try:
            subdirs = next(os.walk(exodosLocation))[1]
            installed_exodos = set()
            for folder in subdirs:
                if folder.startswith("!") or folder.lower() == metadataFolder.lower():
                    continue
                full_p = os.path.join(exodosLocation, folder).replace("\\", "/")
                entry = f"{exodosPrefix}{full_p}"
                installed_exodos.add(folder.lower())
                results.append((entry, 1))

            if includeUninstalled:
                dos_dir = os.path.join(exodosLocation, metadataFolder)
                if os.path.isdir(dos_dir):
                    meta_subdirs = next(os.walk(dos_dir))[1]
                    for folder in meta_subdirs:
                        if folder.startswith("!"):
                            continue
                        if folder.lower() not in installed_exodos:
                            full_p = os.path.join(dos_dir, folder).replace("\\", "/")
                            entry = f"{exodosPrefix}{full_p}"
                            results.append((entry, 0))
        except Exception as e:
            logger.warning(f"Error scanning eXoDOS catalog in scanAllSources: {e}")

    # Deduplicate results: if entry appears multiple times, prefer is_installed == 1
    dedup = {}
    for entry, is_inst in results:
        if entry not in dedup or (is_inst == 1 and dedup[entry] == 0):
            dedup[entry] = is_inst

    return [(k, v) for k, v in dedup.items()]


def chooseGame(content, sampleSize=None):
    """
    Picks a random game from the catalog, giving strong priority to 
    unplayed games or games with the lowest play count.
    """
    if not content:
        return ""

    sampleSize = sampleSize or getattr(__CONFIG__, 'randomSampleSize', 25)
    sampled = random.sample(content, min(sampleSize, len(content)))
    best_candidate = None
    min_played = 999999

    for game in sampled:
        info = findGameInfo(game)
        if info is None:
            return game
        times_played = info[2] or 0
        finished = info[4] or 0
        
        if finished == 1:
            times_played += 100
            
        if times_played < min_played:
            min_played = times_played
            best_candidate = game

    return best_candidate or random.choice(content)

def isGameInstalledOnSystem(gameName, config, playniteInstalledIds=None):
    """
    Verifies if a game from GamesChoosed is still installed on the system.
    Returns tuple: (is_installed: bool, folder_not_empty_warning: bool, warning_message: str)
    Ultra-safe and optimized to avoid COM crashes or deep junction point recursion.
    """
    # 1. Playnite games (instant memory check)
    if gameName.startswith(PLAYNITE_PREFIX):
        parts = gameName.split(":")
        game_id = parts[-1] if len(parts) >= 3 else ""
        if playniteInstalledIds is not None:
            return (game_id in playniteInstalledIds, False, None)
        return (True, False, None)

    # 2. Legacy Steam / GOG in database (cleanup requested, mark false immediately)
    if gameName.startswith("steam:") or gameName.startswith("gog:"):
        return (False, False, None)

    # 3. eXoDOS games
    if gameName.startswith(exodosPrefix):
        target_path = gameName[len(exodosPrefix):]
        if not os.path.isdir(target_path):
            return (False, False, None)
        try:
            with os.scandir(target_path) as it:
                if any(True for _ in it):
                    return (True, False, None)
        except Exception:
            return (False, False, None)
        return (False, False, None)

    # 4. Shortcut links (.lnk / .url) - Safe filesystem check, avoids win32com GPF
    if gameName.startswith(linkPrefix):
        link_path = gameName[len(linkPrefix):]
        try:
            return (os.path.exists(link_path), False, None)
        except Exception:
            return (False, False, None)

    # 5. Local game folders (e.g. D:/Jogos/NomeDoJogo)
    try:
        folder_path = gameName.replace("/", "\\")
        if not os.path.exists(folder_path):
            return (False, False, None)

        if os.path.isdir(folder_path):
            total_files = 0
            subdirs = []

            # Level 1: Root folder
            with os.scandir(folder_path) as it:
                for entry in it:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            total_files += 1
                            if entry.name.lower().endswith(('.exe', '.bat', '.cmd')):
                                return (True, False, None)
                        elif entry.is_dir(follow_symlinks=False):
                            if not entry.name.startswith(('.', '$')):
                                subdirs.append(entry.path)
                    except (PermissionError, OSError):
                        continue

            # Level 2: Immediate subfolders (capped to 10 subdirectories to prevent deep traversal)
            for sdir in subdirs[:10]:
                try:
                    with os.scandir(sdir) as it2:
                        for entry2 in it2:
                            try:
                                if entry2.is_file(follow_symlinks=False):
                                    total_files += 1
                                    if entry2.name.lower().endswith(('.exe', '.bat', '.cmd')):
                                        return (True, False, None)
                            except (PermissionError, OSError):
                                continue
                except (PermissionError, OSError):
                    continue

            if total_files > 0:
                warning = f"A pasta '{folder_path}', apesar do jogo não estar instalado, não está vazia ({total_files} arquivos encontrados)."
                return (False, True, warning)
            return (False, False, None)
    except Exception:
        return (False, False, None)

    return (False, False, None)
