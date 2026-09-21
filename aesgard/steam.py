# -*- coding: utf-8 -*-
"""
Steam integration module for Choose Random Game.
Provides:
- Steam Storefront API cover retrieval (with intelligent title sanitization and fallback)
- Local Steam Grid cover art inspector (userdata/<id>/config/grid)
- Local Steam Library detector (libraryfolders.vdf & appmanifest_*.acf)
- Game launcher via steam://rungameid/{appId}
"""
import os
import re
import json
import logging
import requests
from io import BytesIO
from typing import Optional, List, Dict
from PIL import Image

logger = logging.getLogger(__name__)

DEFAULT_STEAM_PATH = r"C:\Program Files (x86)\Steam"

def cleanSteamTitle(title: str) -> str:
    """Sanitizes game title for Steam Storefront search (removes hyphens, edition tags, clutter)."""
    clean = re.sub(r'\(.*?\)', '', title)
    clean = re.sub(r'\[.*?\]', '', clean)
    clean = clean.replace('.lnk', '').replace('.url', '').replace('.exe', '')
    # Replace hyphens, colons, underscores and plus with spaces so Steam does not treat '-' as NOT
    clean = re.sub(r'[-_:+]', ' ', clean)
    return ' '.join(clean.split()).strip()

def fetchSteamCover(title: str, appId: Optional[str] = None, timeout: int = 5) -> Optional[Image.Image]:
    """
    Queries official Steam Storefront API for high-resolution library or header covers.
    Performs strictly validated title matching to guarantee the cover belongs to the exact game.
    """
    from aesgard.covers import isReliableTitleMatch

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ChooseRandomGame/2.0'
    }

    # If AppID is directly known
    if appId:
        candidates = [
            f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appId}/library_600x900_2x.jpg",
            f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appId}/header.jpg",
            f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appId}/capsule_616x353.jpg"
        ]
        for url in candidates:
            try:
                resp = requests.get(url, headers=headers, timeout=timeout)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    return Image.open(BytesIO(resp.content))
            except Exception:
                continue

    if not title or len(title) < 2:
        return None

    clean_term = cleanSteamTitle(title)
    if not clean_term:
        return None

    queries = [clean_term]
    if ':' in title:
        primary = cleanSteamTitle(title.split(':', 1)[0])
        if primary and primary != clean_term and len(primary.split()) >= 2:
            queries.append(primary)
    elif ' - ' in title:
        primary = cleanSteamTitle(title.split(' - ', 1)[0])
        if primary and primary != clean_term and len(primary.split()) >= 2:
            queries.append(primary)

    for q in queries:
        try:
            url = f"https://store.steampowered.com/api/storesearch/?term={requests.utils.quote(q)}&l=english&cc=US"
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code != 200:
                continue
            data = resp.json()
            if data.get("total", 0) > 0 and data.get("items"):
                for item in data["items"]:
                    cand_name = item.get("name", "")
                    if not isReliableTitleMatch(title, cand_name) and not isReliableTitleMatch(clean_term, cand_name):
                        logger.debug(f"Rejecting Steam search item '{cand_name}' for '{title}'")
                        continue

                    found_id = item.get("id")
                    if not found_id:
                        continue

                    candidates = [
                        f"https://cdn.cloudflare.steamstatic.com/steam/apps/{found_id}/library_600x900_2x.jpg",
                        f"https://cdn.cloudflare.steamstatic.com/steam/apps/{found_id}/header.jpg",
                        f"https://cdn.cloudflare.steamstatic.com/steam/apps/{found_id}/capsule_616x353.jpg",
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
            logger.debug(f"Steam search error for '{q}': {e}")

    return None

def findLocalSteamGridCover(appId: str, steamPath: Optional[str] = None) -> Optional[Image.Image]:
    """
    Checks local Steam client userdata/<id>/config/grid for cached custom cover art.
    """
    root = steamPath or DEFAULT_STEAM_PATH
    userdata = os.path.join(root, "userdata")
    if not os.path.isdir(userdata):
        return None

    try:
        for user_id in os.listdir(userdata):
            grid_dir = os.path.join(userdata, user_id, "config", "grid")
            if os.path.isdir(grid_dir):
                for candidate in (f"{appId}p.jpg", f"{appId}p.png", f"{appId}.jpg", f"{appId}.png"):
                    p = os.path.join(grid_dir, candidate)
                    if os.path.exists(p):
                        try:
                            return Image.open(p)
                        except Exception:
                            pass
    except Exception as e:
        logger.debug(f"Error checking Steam grid: {e}")
    return None

def launchSteamGame(appId: str):
    """Launches game directly through the Steam client protocol."""
    url = f"steam://rungameid/{appId}"
    logger.info(f"Launching Steam game: {url}")
    os.startfile(url)
