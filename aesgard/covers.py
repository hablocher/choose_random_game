# -*- coding: utf-8 -*-
"""
Cover art and icon resolver for Choose Random Game.
Implements a multi-tier fallback strategy to ALWAYS present a game image:
1. Local disk cache (covers_cache/)
2. Playnite database & media storage (library/files)
3. Steam Storefront Database (Public API with automatic caching)
4. Specialized databases (eXoDOS Extras, eXoDOS Boxart, Wikipedia Thumbnails)
5. Executable (.exe) or Shortcut (.lnk) embedded icon extraction via Win32 API
6. Procedural High-Quality Gamer Card Generator (Guaranteed Fallback)
"""
import os
import re
import json
import logging
import requests
import hashlib
from io import BytesIO
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from aesgard.playnite import PLAYNITE_PREFIX, getPlayniteCoverPath
from aesgard.ui import formatDisplayName

logger = logging.getLogger(__name__)

# In-memory dictionary for Playnite title-to-cover mapping
_PLAYNITE_TITLE_MAP = None

def getCleanGameTitle(gameEntry: str) -> str:
    """Extracts a clean, searchable game title from any game entry."""
    # Playnite: playnite:Source:Name:Id
    if gameEntry.startswith(PLAYNITE_PREFIX):
        parts = gameEntry.split(":")
        if len(parts) >= 3:
            return formatDisplayName(parts[2])
    
    # Raw name
    name = formatDisplayName(gameEntry)
    # Remove common clutter
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'\[.*?\]', '', name)
    name = name.replace('.lnk', '').replace('.url', '').replace('.exe', '')
    return name.strip()

def getCachePath(gameEntry: str, cacheDir: str = "covers_cache") -> str:
    """Generates a stable cache filename for a given game entry."""
    clean_title = getCleanGameTitle(gameEntry)
    slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', clean_title.lower())[:40]
    hash_id = hashlib.md5(gameEntry.encode('utf-8', errors='ignore')).hexdigest()[:8]
    filename = f"{slug}_{hash_id}.jpg"
    return os.path.join(cacheDir, filename)

def loadPlayniteTitleMap(playnitePath: str, exportJsonPath: str = "playnite_games.json") -> dict:
    """Caches Playnite games by normalized title for cross-platform local matching."""
    global _PLAYNITE_TITLE_MAP
    if _PLAYNITE_TITLE_MAP is not None:
        return _PLAYNITE_TITLE_MAP

    _PLAYNITE_TITLE_MAP = {}
    if not exportJsonPath or not os.path.exists(exportJsonPath):
        return _PLAYNITE_TITLE_MAP

    try:
        with open(exportJsonPath, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
            for item in data:
                title = item.get("name", "").strip().lower()
                game_id = item.get("id", "")
                if title and game_id:
                    _PLAYNITE_TITLE_MAP[title] = game_id
    except Exception as e:
        logger.debug(f"Could not build Playnite title map: {e}")

    return _PLAYNITE_TITLE_MAP

def fetchFromSteamStore(cleanTitle: str, timeout: int = 5) -> Optional[Image.Image]:
    """Queries public Steam Storefront search API for official game capsule/header."""
    if not cleanTitle or len(cleanTitle) < 2:
        return None

    try:
        url = f"https://store.steampowered.com/api/storesearch/?term={requests.utils.quote(cleanTitle)}&l=english&cc=US"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ChooseRandomGame/2.0'}
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return None

        data = resp.json()
        if data.get("total", 0) > 0 and data.get("items"):
            item = data["items"][0]
            appid = item.get("id")
            if not appid:
                return None

            # Try library cover, then header, then capsule
            candidates = [
                f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900_2x.jpg",
                f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg",
                f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/capsule_616x353.jpg",
                item.get("tiny_image", "")
            ]

            for img_url in candidates:
                if not img_url:
                    continue
                try:
                    img_resp = requests.get(img_url, headers=headers, timeout=timeout)
                    if img_resp.status_code == 200 and len(img_resp.content) > 1000:
                        return Image.open(BytesIO(img_resp.content))
                except Exception:
                    continue
    except Exception as e:
        logger.debug(f"Steam cover search failed for '{cleanTitle}': {e}")

    return None

def fetchFromWikipedia(cleanTitle: str, timeout: int = 4) -> Optional[Image.Image]:
    """Fallback query to Wikipedia REST API for game summary thumbnail."""
    if not cleanTitle:
        return None
    try:
        query = f"{cleanTitle} (video game)"
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(query)}"
        headers = {'User-Agent': 'ChooseRandomGame/2.0'}
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code == 200:
            thumb = r.json().get("thumbnail", {}).get("source")
            if thumb:
                img_r = requests.get(thumb, headers=headers, timeout=timeout)
                if img_r.status_code == 200:
                    return Image.open(BytesIO(img_r.content))
    except Exception:
        pass
    return None

def generateProceduralCover(title: str, size: Tuple[int, int] = (160, 160)) -> Image.Image:
    """Generates an aesthetic, dynamic dark-mode gamer card when no image is found anywhere."""
    w, h = size
    # Create smooth dark gradient
    base = Image.new("RGBA", (w, h), (18, 21, 29, 255))
    draw = ImageDraw.Draw(base)

    # Accent color derived deterministically from title
    h_val = int(hashlib.md5(title.encode('utf-8')).hexdigest()[:6], 16)
    r = 20 + (h_val % 40)
    g = 130 + ((h_val >> 4) % 90)
    b = 180 + ((h_val >> 8) % 75)
    accent = (r, g, b, 255)

    # Draw border & header bar
    draw.rounded_rectangle([4, 4, w - 5, h - 5], radius=10, outline=accent, width=2)
    draw.rounded_rectangle([8, 8, w - 9, 32], radius=6, fill=(26, 32, 44, 255))

    # Draw small Gamepad symbol / text
    draw.text((14, 12), "🎮 GAME", fill=accent)

    # Wrap title across 3 lines max
    words = title.split()
    lines = []
    curr = []
    for word in words:
        if len(" ".join(curr + [word])) <= 14:
            curr.append(word)
        else:
            lines.append(" ".join(curr))
            curr = [word]
            if len(lines) >= 3:
                break
    if curr and len(lines) < 3:
        lines.append(" ".join(curr))

    y_start = (h // 2) - (len(lines) * 10)
    for i, line in enumerate(lines):
        draw.text((14, y_start + (i * 18)), line, fill=(226, 232, 240, 255))

    return base.convert("RGB")

def resolveGameCover(gameEntry: str, 
                     config=None, 
                     targetSize: Tuple[int, int] = (160, 160),
                     win32_extractor=None) -> Image.Image:
    """
    Multi-tier cover art resolution:
    1. Local cache lookup
    2. Playnite media database
    3. Steam Storefront public database
    4. eXoDOS / Wikipedia / web metadata
    5. Embedded Win32 executable/shortcut icon
    6. Procedural gamer card (Guaranteed fallback)
    """
    if not gameEntry:
        return generateProceduralCover("Jogo", targetSize)

    clean_title = getCleanGameTitle(gameEntry)
    cache_dir = getattr(config, 'coversCacheDir', 'covers_cache')
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = getCachePath(gameEntry, cache_dir)

    # 1. Local Cache Lookup
    if os.path.exists(cache_file):
        try:
            img = Image.open(cache_file)
            img.load()
            # If cached image is a tiny fallback icon (<= 48x48) and online is enabled, allow upgrading
            if getattr(config, 'fetchOnlineCovers', True) and img.width <= 48 and img.height <= 48:
                pass
            else:
                return img.resize(targetSize)
        except Exception:
            pass

    found_img: Optional[Image.Image] = None

    # 2. Playnite Database Lookup
    playnite_path = getattr(config, 'playnitePath', '')
    lib_files_dir = getattr(config, 'playniteLibraryFilesDir', 'library/files')

    # If it's a native Playnite entry
    if gameEntry.startswith(PLAYNITE_PREFIX):
        parts = gameEntry.split(":")
        game_id = parts[-1] if len(parts) >= 3 else ""
        if playnite_path and game_id:
            cover_path = getPlayniteCoverPath(playnite_path, game_id, libraryFilesDir=lib_files_dir)
            if cover_path and os.path.exists(cover_path):
                try:
                    found_img = Image.open(cover_path)
                except Exception:
                    pass

    # If it's another source, check if title exists in Playnite export
    if not found_img and playnite_path:
        export_json = getattr(config, 'playniteExportJson', 'playnite_games.json')
        title_map = loadPlayniteTitleMap(playnite_path, export_json)
        norm_title = clean_title.lower()
        if norm_title in title_map:
            p_id = title_map[norm_title]
            cover_path = getPlayniteCoverPath(playnite_path, p_id, libraryFilesDir=lib_files_dir)
            if cover_path and os.path.exists(cover_path):
                try:
                    found_img = Image.open(cover_path)
                except Exception:
                    pass

    # 3. GOG & Steam Official Databases (Catalog & Storefront APIs + Local Folders)
    fetch_online = getattr(config, 'fetchOnlineCovers', True)
    gog_enabled = getattr(config, 'gogEnabled', True)
    steam_enabled = getattr(config, 'steamEnabled', True)

    is_gog_hint = "gog" in gameEntry.lower()
    is_steam_hint = "steam" in gameEntry.lower()

    # Local GOG folder inspection
    if not found_img and is_gog_hint:
        try:
            from aesgard.gog import findGOGGameFolderCover
            raw_path = gameEntry[len("link::"):] if gameEntry.startswith("link::") else gameEntry
            folder_candidate = os.path.dirname(raw_path) if os.path.isfile(raw_path) else raw_path
            found_img = findGOGGameFolderCover(folder_candidate)
        except Exception:
            pass

    # GOG Catalog search (priority for GOG games or general shortcuts)
    if not found_img and fetch_online and gog_enabled:
        if is_gog_hint or not is_steam_hint:
            try:
                from aesgard.gog import fetchGOGCover
                found_img = fetchGOGCover(clean_title)
            except Exception as e:
                logger.debug(f"GOG cover search failed: {e}")

    # Steam Storefront search (with sanitized queries avoiding fulltext exclusion)
    if not found_img and fetch_online and steam_enabled:
        try:
            from aesgard.steam import fetchSteamCover
            found_img = fetchSteamCover(clean_title)
        except Exception as e:
            logger.debug(f"Steam cover search failed: {e}")

    # GOG fallback if Steam was checked first
    if not found_img and fetch_online and gog_enabled and is_steam_hint:
        try:
            from aesgard.gog import fetchGOGCover
            found_img = fetchGOGCover(clean_title)
        except Exception as e:
            logger.debug(f"GOG fallback cover search failed: {e}")

    # 4. Specialized eXoDOS / Wikipedia Databases
    if not found_img and ("exodos" in gameEntry.lower() or gameEntry.startswith("exodos:")):
        exodos_loc = getattr(config, 'EXODOSLocation', '')
        metadata_folder = getattr(config, 'EXODOSMetadataFolder', '!dos')
        target_dir = gameEntry[7:] if gameEntry.startswith("exodos:") else gameEntry
        folder_name = os.path.basename(target_dir.rstrip("/\\"))
        
        candidates = [
            target_dir,
            os.path.join(target_dir, "Extras"),
            os.path.join(exodos_loc, metadata_folder, folder_name),
            os.path.join(exodos_loc, metadata_folder, folder_name, "Extras")
        ]
        for c in candidates:
            if os.path.isdir(c):
                try:
                    for f in os.listdir(c):
                        if f.lower().endswith(('.jpg', '.png', '.ico')):
                            found_img = Image.open(os.path.join(c, f))
                            break
                except Exception:
                    pass
            if found_img:
                break

    if not found_img and fetch_online:
        found_img = fetchFromWikipedia(clean_title)

    # 5. Executable (.exe) or Shortcut (.lnk) Embedded Icon
    if not found_img and win32_extractor is not None:
        try:
            ico = win32_extractor(gameEntry, targetSize)
            if ico:
                found_img = ico
        except Exception:
            pass

    # 6. Procedural Fallback Card (Zero-fail guarantee)
    if not found_img:
        found_img = generateProceduralCover(clean_title, targetSize)

    # Save to disk cache for instantaneous future access
    try:
        found_img_rgb = found_img.convert("RGB").resize(targetSize)
        found_img_rgb.save(cache_file, "JPEG", quality=90)
        return found_img_rgb
    except Exception:
        return found_img.convert("RGB").resize(targetSize)
