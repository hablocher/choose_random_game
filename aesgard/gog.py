# -*- coding: utf-8 -*-
"""
GOG integration module for Choose Random Game.
Provides:
- GOG official catalog search & cover art retrieval via GOG CDN
- Local GOG Galaxy database reader (galaxy-2.0.db)
- Local installation folder inspector (goggame-*.info / goggame-*.ico)
- Game launcher via GOG Galaxy URI or standalone executable
"""
import os
import re
import json
import logging
import sqlite3
import requests
from io import BytesIO
from typing import Optional, List, Dict
from PIL import Image

logger = logging.getLogger(__name__)

DEFAULT_GALAXY_DB_PATH = os.path.expandvars(r"%PROGRAMDATA%\GOG.com\Galaxy\storage\galaxy-2.0.db")

def cleanGOGTitle(title: str) -> str:
    """Prepares a clean search query for GOG catalog API."""
    clean = re.sub(r'\(.*?\)', '', title)
    clean = re.sub(r'\[.*?\]', '', clean)
    clean = clean.replace('.lnk', '').replace('.url', '').replace('.exe', '')
    # Replace separators with spaces
    clean = re.sub(r'[-_:+]', ' ', clean)
    return ' '.join(clean.split()).strip()

def fetchGOGCover(title: str, timeout: int = 5) -> Optional[Image.Image]:
    """
    Queries official GOG Catalog API for high-resolution vertical or horizontal cover art.
    Performs strictly validated title matching to guarantee the cover belongs to the exact game.
    """
    from aesgard.covers import isReliableTitleMatch

    if not title or len(title) < 2:
        return None

    clean_term = cleanGOGTitle(title)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ChooseRandomGame/2.0',
        'Accept': 'application/json'
    }

    # Query variations: 1. Full clean term; 2. Primary title before colon/hyphen if available
    queries = [clean_term]
    if ':' in title:
        primary = cleanGOGTitle(title.split(':', 1)[0])
        if primary and primary != clean_term and len(primary.split()) >= 2:
            queries.append(primary)
    elif ' - ' in title:
        primary = cleanGOGTitle(title.split(' - ', 1)[0])
        if primary and primary != clean_term and len(primary.split()) >= 2:
            queries.append(primary)

    for q in queries:
        try:
            # 1. Official GOG Catalog v1 API
            catalog_url = f"https://catalog.gog.com/v1/catalog?query={requests.utils.quote(q)}&limit=5"
            resp = requests.get(catalog_url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                products = data.get("products", [])
                for prod in products:
                    prod_title = prod.get("title", "")
                    if not isReliableTitleMatch(title, prod_title) and not isReliableTitleMatch(clean_term, prod_title):
                        logger.debug(f"Rejecting GOG catalog product '{prod_title}' for '{title}'")
                        continue

                    # Candidates in order of quality
                    img_candidates = [
                        prod.get("coverVertical"),
                        prod.get("coverHorizontal"),
                        prod.get("galaxyBackgroundImage")
                    ]
                    for img_url in img_candidates:
                        if img_url:
                            # Replace formatter placeholder if present
                            real_url = img_url.replace("_{formatter}.jpg", ".jpg").replace("_{formatter}.png", ".png")
                            try:
                                img_resp = requests.get(real_url, headers=headers, timeout=timeout)
                                if img_resp.status_code == 200 and len(img_resp.content) > 1000:
                                    return Image.open(BytesIO(img_resp.content))
                            except Exception:
                                continue

            # 2. GOG Embed Ajax Filtered Search (Fallback)
            embed_url = f"https://embed.gog.com/games/ajax/filtered?mediaType=game&search={requests.utils.quote(q)}"
            resp_embed = requests.get(embed_url, headers=headers, timeout=timeout)
            if resp_embed.status_code == 200:
                data = resp_embed.json()
                products = data.get("products", [])
                for prod in products:
                    prod_title = prod.get("title", "")
                    if not isReliableTitleMatch(title, prod_title) and not isReliableTitleMatch(clean_term, prod_title):
                        logger.debug(f"Rejecting GOG embed product '{prod_title}' for '{title}'")
                        continue

                    img_url = prod.get("image")
                    if img_url:
                        # GOG embed image urls typically start with //
                        if img_url.startswith("//"):
                            img_url = f"https:{img_url}"
                        if not img_url.endswith((".jpg", ".png")):
                            img_url = f"{img_url}_glx_vertical_cover.jpg"
                        try:
                            img_resp = requests.get(img_url, headers=headers, timeout=timeout)
                            if img_resp.status_code == 200 and len(img_resp.content) > 1000:
                                return Image.open(BytesIO(img_resp.content))
                        except Exception:
                            pass
        except Exception as e:
            logger.debug(f"GOG cover search error for '{q}': {e}")

    return None

def findGOGGameFolderCover(gameDir: str) -> Optional[Image.Image]:
    """
    Inspects a local GOG game installation folder for goggame-*.ico or art files.
    """
    if not os.path.isdir(gameDir):
        return None
    try:
        for f in os.listdir(gameDir):
            f_lower = f.lower()
            if f_lower.startswith("goggame-") and f_lower.endswith((".ico", ".png", ".jpg")):
                return Image.open(os.path.join(gameDir, f))
            if f_lower in ("cover.jpg", "cover.png", "boxart.jpg", "icon.ico"):
                return Image.open(os.path.join(gameDir, f))
    except Exception as e:
        logger.debug(f"Error inspecting GOG folder '{gameDir}': {e}")
    return None

def getGOGGalaxyGames(dbPath: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Reads locally installed and owned games directly from GOG Galaxy SQLite database.
    """
    path = dbPath or DEFAULT_GALAXY_DB_PATH
    if not os.path.exists(path):
        return []

    games = []
    try:
        uri = f"file:{os.path.abspath(path)}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT gp1.releaseKey, gp1.value 
            FROM GamePieces gp1
            JOIN InstalledExternalProducts iep ON iep.productId = gp1.releaseKey
            WHERE gp1.gamePieceTypeId = 2;
        """)
        for r in cur.fetchall():
            games.append({"releaseKey": str(r[0]), "title": str(r[1])})
        conn.close()
    except Exception as e:
        logger.debug(f"Could not read GOG Galaxy database: {e}")

    return games

def launchGOGGame(releaseKeyOrId: str):
    """Launches a game via GOG Galaxy client protocol."""
    url = f"goggalaxy://openGameView/{releaseKeyOrId}"
    logger.info(f"Launching GOG game: {url}")
    os.startfile(url)
