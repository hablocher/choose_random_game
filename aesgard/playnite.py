# -*- coding: utf-8 -*-
"""
Playnite integration module for Choose Random Game.
Supports reading games from Playnite and launching them via the playnite:// URI protocol.
"""
import os
import json
import logging
import webbrowser

logger = logging.getLogger(__name__)
PLAYNITE_PREFIX = "playnite:"

def getDefaultPlaynitePath():
    """Detect default Playnite installation/library paths."""
    candidates = [
        r"E:\Util\Playnite",
        os.path.expandvars(r"%APPDATA%\Playnite"),
        os.path.expandvars(r"%LOCALAPPDATA%\Playnite"),
        r"C:\Program Files\Playnite",
        r"C:\Program Files (x86)\Playnite",
    ]
    for path in candidates:
        if os.path.exists(path) and (
            os.path.exists(os.path.join(path, "library")) or 
            os.path.exists(os.path.join(path, "Playnite.DesktopApp.exe"))
        ):
            return path
    return ""

def loadPlayniteGames(playnitePath, onlyInstalled=True, exportJsonPath=None):
    """
    Loads Playnite games. 
    Checks for an exported JSON file first (fastest and immune to file locks).
    Falls back to checking the export in the project folder or Playnite library directory.
    
    Returns a list of dicts: [{'id': ..., 'name': ..., 'cover': ..., 'is_installed': ...}]
    """
    games = []
    
    # 1. Look for pre-exported JSON in project directory or specified path
    potential_json_paths = []
    if exportJsonPath and os.path.exists(exportJsonPath):
        potential_json_paths.append(exportJsonPath)
        
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    potential_json_paths.extend([
        os.path.join(project_dir, "playnite_games.json"),
        os.path.join(playnitePath, "playnite_games.json") if playnitePath else "",
        os.path.join(playnitePath, "library", "playnite_games.json") if playnitePath else "",
    ])
    
    loaded_from_json = False
    for json_file in potential_json_paths:
        if json_file and os.path.exists(json_file):
            try:
                with open(json_file, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                    for item in data:
                        is_installed = item.get("IsInstalled", item.get("is_installed", True))
                        if onlyInstalled and not is_installed:
                            continue
                        games.append({
                            "id": item.get("Id", item.get("id", "")),
                            "name": item.get("Name", item.get("name", "Unknown")),
                            "cover": item.get("CoverImage", item.get("cover", "")),
                            "icon": item.get("Icon", item.get("icon", "")),
                            "is_installed": is_installed,
                            "platform": item.get("Platform", item.get("platform", "")),
                            "source": item.get("Source", item.get("source", "Playnite")),
                        })
                    if games:
                        logger.info(f"Loaded {len(games)} games from Playnite export: {json_file}")
                        loaded_from_json = True
                        break
            except Exception as e:
                logger.warning(f"Error reading Playnite JSON export ({json_file}): {e}")

    # 2. If no games loaded, attempt auto-export from Playnite LiteDB
    if not games and playnitePath:
        db_path = os.path.join(playnitePath, "library", "games.db")
        dll_path = os.path.join(playnitePath, "LiteDB.dll")
        script_path = os.path.join(project_dir, "export_playnite_library.ps1")
        if os.path.exists(db_path) and os.path.exists(dll_path) and os.path.exists(script_path):
            try:
                import subprocess
                target_json = os.path.join(project_dir, "playnite_games.json")
                logger.info(f"Triggering automatic Playnite library export via {script_path}...")
                cmd = [
                    "powershell", "-ExecutionPolicy", "Bypass", "-File", script_path,
                    "-PlaynitePath", playnitePath,
                    "-OutputFile", target_json
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                if os.path.exists(target_json):
                    with open(target_json, "r", encoding="utf-8-sig") as f:
                        data = json.load(f)
                        for item in data:
                            is_installed = item.get("IsInstalled", item.get("is_installed", True))
                            if onlyInstalled and not is_installed:
                                continue
                            games.append({
                                "id": item.get("Id", item.get("id", "")),
                                "name": item.get("Name", item.get("name", "Unknown")),
                                "cover": item.get("CoverImage", item.get("cover", "")),
                                "icon": item.get("Icon", item.get("icon", "")),
                                "is_installed": is_installed,
                            })
                        logger.info(f"Auto-export loaded {len(games)} installed games from Playnite.")
            except Exception as se:
                logger.warning(f"Auto-export from Playnite LiteDB failed: {se}")

    return games

loadPlayniteLibrary = loadPlayniteGames

def formatPlayniteEntries(games, includeInstalledFlag=False):
    """Formats Playnite games into choose_random_game string entries or (entry, is_installed) tuples."""
    entries = []
    for g in games:
        # Format: playnite:Game Name:GameId
        entry = f"{PLAYNITE_PREFIX}{g['name']}:{g['id']}"
        if includeInstalledFlag:
            entries.append((entry, 1 if g.get("is_installed") else 0))
        else:
            entries.append(entry)
    return entries

def launchPlayniteGame(gameId, uriPrefix="playnite://playnite/start/"):
    """Launches a game via Playnite URI protocol."""
    uri = f"{uriPrefix.rstrip('/')}/{gameId}"
    logger.info(f"Launching Playnite game ID {gameId} via {uri}")
    try:
        os.startfile(uri)
        return True
    except Exception as e:
        logger.error(f"Error launching Playnite game via URI: {e}")
        try:
            webbrowser.open(uri)
            return True
        except Exception as we:
            logger.error(f"Fallback launch failed: {we}")
            return False

def installPlayniteGame(gameId: str) -> bool:
    """Prompts Playnite to install the game via playnite://playnite/install/<id>."""
    uri = f"playnite://playnite/install/{gameId}"
    logger.info(f"Triggering Playnite install for ID {gameId} via {uri}")
    try:
        os.startfile(uri)
        return True
    except Exception as e:
        logger.error(f"Error triggering Playnite install: {e}")
        try:
            import webbrowser
            webbrowser.open(uri)
            return True
        except Exception as we:
            logger.error(f"Fallback install launch failed: {we}")
            return False

def getPlayniteCoverPath(playnitePath, coverImageOrGameId, libraryFilesDir="library/files"):
    """
    Finds the cover image path in Playnite's library files directory.
    Supports:
    - Direct relative path: 'guid/image.jpg'
    - Game ID directory: '00054f73-755c-41a4-81b5-a5e4d2e189ca' (inspects directory for portrait cover)
    - Image GUID directly
    """
    if not playnitePath or not coverImageOrGameId:
        return None

    base_dir = os.path.join(playnitePath, libraryFilesDir.replace("/", os.sep))
    direct_path = os.path.join(base_dir, coverImageOrGameId)

    # 1. Direct file match
    if os.path.isfile(direct_path):
        return direct_path

    # 2. Game folder match: inspect images inside and prioritize portrait cover art
    if os.path.isdir(direct_path):
        try:
            from PIL import Image as PilImage
            candidates = []
            for f in os.listdir(direct_path):
                f_lower = f.lower()
                if f_lower.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    full_f = os.path.join(direct_path, f)
                    try:
                        with PilImage.open(full_f) as im:
                            w, h = im.size
                            is_portrait = (h >= w)
                            candidates.append((is_portrait, h * w, full_f))
                    except Exception:
                        candidates.append((False, 0, full_f))
            
            if candidates:
                # Sort: prioritize portrait covers, then highest resolution
                candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
                return candidates[0][2]
        except Exception as e:
            logger.debug(f"Error resolving cover from Playnite folder {direct_path}: {e}")

    return None

