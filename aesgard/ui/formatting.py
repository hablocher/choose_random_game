# -*- coding: utf-8 -*-
"""
Formatting and platform detection utilities for game titles and metadata.
"""
import os
import logging

logger = logging.getLogger(__name__)

_PLAYNITE_META_CACHE = None


def clearPlayniteMetaCache():
    """Clears cached Playnite metadata to force reload from playnite_games.json."""
    global _PLAYNITE_META_CACHE
    _PLAYNITE_META_CACHE = None


def _getPlayniteMetaCache():
    global _PLAYNITE_META_CACHE
    if _PLAYNITE_META_CACHE is None:
        _PLAYNITE_META_CACHE = {}
        # project directory
        project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        json_path = os.path.join(project_dir, "playnite_games.json")
        if os.path.exists(json_path):
            try:
                import json
                with open(json_path, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                    for item in data:
                        gid = item.get("Id") or item.get("id")
                        if gid:
                            _PLAYNITE_META_CACHE[gid] = {
                                "platform": item.get("Platform") or "",
                                "source": item.get("Source") or "Playnite"
                            }
            except Exception:
                pass
    return _PLAYNITE_META_CACHE


def formatDisplayName(rawName: str) -> str:
    """Generates a clean, human-readable display title from raw game entry."""
    if not rawName:
        return ""
    name = str(rawName)
    if name.startswith("playnite:"):
        parts = name.split(":")
        if len(parts) >= 2:
            return parts[1]
    elif name.startswith("steam:"):
        parts = name.split(":")
        if len(parts) >= 2:
            return parts[1]
    elif name.startswith("exodos:"):
        path = name[len("exodos:"):]
        try:
            from aesgard.gameutil import geteXoDOSGameDetails
            _, title = geteXoDOSGameDetails(path)
            return f"[eXoDOS] {title}"
        except Exception:
            return f"[eXoDOS] {os.path.basename(path.rstrip('/\\'))}"
    elif name.startswith("link::"):
        clean = name[len("link::"):]
        basename = os.path.basename(clean)
        return os.path.splitext(basename)[0]
    elif name.startswith("gog:"):
        return f"[GOG] {name[4:]}"
    else:
        # Local folder path
        clean = name.replace("\\", "/").rstrip("/")
        folder_title = clean.split("/")[-1]
        if "dosbox" in clean.lower():
            return f"[DOSBox] {folder_title}"
        return folder_title
    return name


def detectPlatform(rawName: str) -> str:
    """Detects the platform/source of a game entry with emulator and store awareness."""
    name_str = str(rawName)
    if name_str.startswith("playnite:"):
        parts = name_str.split(":")
        if len(parts) >= 3:
            game_id = parts[-1]
            cache = _getPlayniteMetaCache()
            if game_id in cache:
                meta = cache[game_id]
                plat = meta.get("platform", "")
                src = meta.get("source", "")
                if plat and "PC" not in plat:
                    return plat
                if src and src != "Playnite":
                    return src
                if plat:
                    return plat
        return "Playnite"
    elif name_str.startswith("steam:"):
        return "Steam"
    elif name_str.startswith("exodos:") or "exodos" in name_str.lower():
        return "eXoDOS"
    elif name_str.startswith("link::"):
        return "Atalho / Desktop"
    elif "dosbox" in name_str.lower():
        return "DOSBox"
    elif name_str.startswith("gog:"):
        return "GOG"
    else:
        return "Instalação Local"


def getPlatformColor(platform: str) -> str:
    """Returns a distinct badge color for each platform/console/store."""
    plat_lower = platform.lower()
    
    # Consoles & Emulators
    if "nintendo 64" in plat_lower or "n64" in plat_lower:
        return "#c0392b"
    if "snes" in plat_lower:
        return "#8e44ad"
    if "playstation 2" in plat_lower or "ps2" in plat_lower:
        return "#1e3799"
    if "playstation" in plat_lower or "ps1" in plat_lower:
        return "#2980b9"
    if "game boy" in plat_lower or "gba" in plat_lower:
        return "#5f27cd"
    if "gamecube" in plat_lower:
        return "#4834d4"
    if "switch" in plat_lower:
        return "#eb4d4b"
    if "sega" in plat_lower or "genesis" in plat_lower or "dreamcast" in plat_lower:
        return "#0984e3"
    if "nintendo" in plat_lower:
        return "#d63031"

    # Stores & Sources
    colors = {
        "Steam": "#1b2838",
        "eXoDOS": "#744210",
        "Playnite": "#ff6b6b",
        "Atalho / Desktop": "#2c3e50",
        "DOSBox": "#4a5568",
        "GOG": "#4b1e78",
        "Epic": "#2d3436",
        "Epic Games": "#2d3436",
        "Xbox": "#107c10",
        "Amazon": "#e67e22",
        "Amazon Games": "#e67e22",
        "Ubisoft": "#0984e3",
        "Ubisoft Connect": "#0984e3",
        "EA app": "#ff4757",
        "Battle.net": "#00a8ff",
        "Riot Games": "#eb4d4b",
        "Legacy Games": "#2c3e50",
        "Instalação Local": "#1a365d"
    }
    return colors.get(platform, "#2d3748")
