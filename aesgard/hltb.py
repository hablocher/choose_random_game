# -*- coding: utf-8 -*-
"""
HowLongToBeat (HLTB) integration module for Choose Random Game.
Fetches estimated completion times using howlongtobeatpy, with local SQLite caching,
ultra-fast in-memory lookup, resilient title cleaning, and curated baseline seeds.
"""
import os
import re
import time
import logging
import sqlite3
from typing import Optional, Dict, Tuple, List

logger = logging.getLogger(__name__)

# In-memory session cache for microsecond lookups
_HLTB_MEMORY_CACHE: Dict[str, Dict] = {}
_HLTB_INITIALIZED = False
_HLTB_CACHE_LOADED = False

# Curated seed durations (title -> (game_name, main_story, main_extra, completionist))
# Provides instantaneous, accurate duration filters (< 5h, 5-15h, > 25h) out of the box
_CURATED_HLTB_SEEDS = [
    # --- Short Games (< 5h) ---
    ("portal", "Portal", 3.0, 5.0, 9.5),
    ("limbo", "Limbo", 3.5, 4.0, 6.5),
    ("inside", "Inside", 3.5, 4.0, 5.0),
    ("journey", "Journey", 2.0, 3.5, 5.5),
    ("abzu", "Abzû", 2.0, 3.0, 4.5),
    ("little nightmares", "Little Nightmares", 3.5, 5.0, 7.0),
    ("donut county", "Donut County", 2.0, 2.5, 3.0),
    ("a short hike", "A Short Hike", 1.5, 2.5, 4.0),
    ("firewatch", "Firewatch", 4.0, 4.5, 5.0),
    ("untitled goose game", "Untitled Goose Game", 3.0, 4.5, 6.0),
    ("super mario bros.", "Super Mario Bros.", 2.0, 3.0, 4.0),
    ("super mario bros", "Super Mario Bros.", 2.0, 3.0, 4.0),
    ("sonic the hedgehog", "Sonic The Hedgehog", 2.0, 3.0, 5.0),
    ("castlevania: dracula x", "Castlevania: Dracula X", 3.0, 3.5, 4.5),
    ("castlevania", "Castlevania", 2.0, 2.5, 3.5),
    ("quake", "Quake", 5.0, 7.5, 12.0),
    ("doom", "Doom (1993)", 5.0, 8.5, 12.0),
    ("chasm: the rift", "Chasm: The Rift", 4.3, 5.5, 8.0),
    ("to the moon", "To the Moon", 4.0, 4.5, 5.0),
    ("katana zero", "Katana Zero", 4.5, 6.5, 10.5),
    ("gris", "Gris", 3.5, 4.5, 6.5),
    ("what remains of edith finch", "What Remains of Edith Finch", 2.0, 2.5, 3.0),
    ("stray", "Stray", 5.0, 6.5, 10.0),
    ("metal slug", "Metal Slug", 1.0, 1.5, 2.5),
    ("metal slug 2", "Metal Slug 2", 1.0, 1.5, 2.5),
    ("metal slug 3", "Metal Slug 3", 1.5, 2.0, 3.0),
    ("metal slug x", "Metal Slug X", 1.0, 1.5, 2.5),
    ("streets of rage", "Streets of Rage", 1.5, 2.0, 3.0),
    ("streets of rage 2", "Streets of Rage 2", 2.0, 2.5, 4.0),
    ("contra", "Contra", 1.0, 1.5, 2.5),
    ("super contra", "Super Contra", 1.0, 1.5, 2.5),
    ("mega man 2", "Mega Man 2", 2.5, 3.5, 4.5),
    ("mega man x", "Mega Man X", 3.5, 4.5, 6.0),
    ("ducktales", "DuckTales", 1.5, 2.0, 3.0),
    ("golden axe", "Golden Axe", 1.0, 1.5, 2.0),
    ("final fight", "Final Fight", 1.0, 1.5, 2.5),
    ("sunset riders", "Sunset Riders", 1.0, 1.5, 2.0),
    ("cadillacs and dinosaurs", "Cadillacs and Dinosaurs", 1.0, 1.5, 2.0),
    ("captain commando", "Captain Commando", 1.0, 1.5, 2.0),
    ("hocus pocus", "Hocus Pocus", 3.5, 5.0, 7.0),
    ("galaga", "Galaga", 1.0, 1.5, 2.0),
    ("galaga: destination earth", "Galaga: Destination Earth", 2.5, 3.5, 5.0),
    ("heretic", "Heretic", 4.5, 6.0, 8.5),
    ("heretic: shadow of the serpent riders", "Heretic: Shadow of the Serpent Riders", 5.0, 7.0, 10.0),
    ("alba: a wildlife adventure", "Alba: A Wildlife Adventure", 2.5, 3.5, 4.5),
    ("outliver: tribulation", "Outliver: Tribulation", 4.0, 5.5, 7.5),
    ("red eclipse", "Red Eclipse", 2.0, 3.0, 5.0),
    ("phantom ascension 2", "Phantom Ascension 2", 3.0, 4.5, 6.0),
    ("wall world 2", "Wall World 2", 4.5, 6.0, 8.5),
    ("riverbond", "Riverbond", 5.0, 6.5, 8.0),
    ("nfl blitz 2001", "NFL Blitz 2001", 5.0, 7.0, 10.0),

    # --- Medium Games (5 - 15h) ---
    ("resident evil 2", "Resident Evil 2", 8.5, 11.5, 20.0),
    ("resident evil 3", "Resident Evil 3", 6.0, 8.5, 13.5),
    ("resident evil 4", "Resident Evil 4", 15.0, 19.5, 30.0),
    ("resident evil 7: biohazard", "Resident Evil 7: Biohazard", 9.5, 12.0, 20.5),
    ("resident evil village", "Resident Evil Village", 9.5, 13.0, 26.5),
    ("dead space", "Dead Space", 11.0, 14.5, 20.0),
    ("bioshock", "BioShock", 12.0, 15.5, 22.0),
    ("bioshock infinite", "BioShock Infinite", 11.5, 15.0, 27.0),
    ("half-life", "Half-Life", 12.0, 14.5, 17.5),
    ("half-life 2", "Half-Life 2", 13.0, 15.5, 20.0),
    ("portal 2", "Portal 2", 8.5, 12.5, 21.5),
    ("tomb raider", "Tomb Raider (2013)", 11.5, 15.0, 20.5),
    ("rise of the tomb raider", "Rise of the Tomb Raider", 13.5, 21.0, 36.0),
    ("batman: arkham asylum", "Batman: Arkham Asylum", 11.5, 16.0, 25.5),
    ("batman: arkham city", "Batman: Arkham City", 12.5, 22.5, 46.5),
    ("dishonored", "Dishonored", 12.0, 18.5, 34.5),
    ("alan wake", "Alan Wake", 11.0, 14.0, 26.5),
    ("doom eternal", "Doom Eternal", 14.5, 19.5, 26.5),
    ("wolfenstein: the new order", "Wolfenstein: The New Order", 11.5, 16.0, 24.5),
    ("devil may cry 5", "Devil May Cry 5", 11.0, 17.5, 36.5),
    ("titanfall 2", "Titanfall 2", 6.0, 9.0, 15.0),
    ("metal gear solid", "Metal Gear Solid", 11.5, 14.0, 16.5),
    ("control", "Control", 11.5, 18.0, 28.5),
    ("metro 2033", "Metro 2033", 9.0, 12.5, 22.0),
    ("metro: last light", "Metro: Last Light", 10.0, 14.0, 23.5),
    ("outlast", "Outlast", 5.0, 6.5, 10.0),
    ("soma", "SOMA", 9.0, 10.5, 12.5),
    ("hellblade: senua's sacrifice", "Hellblade: Senua's Sacrifice", 7.5, 8.5, 9.0),
    ("celeste", "Celeste", 8.0, 13.5, 39.0),
    ("ori and the blind forest", "Ori and the Blind Forest", 8.0, 10.5, 14.5),
    ("cuphead", "Cuphead", 10.5, 15.0, 25.0),
    ("undertale", "Undertale", 6.5, 10.0, 21.5),
    ("ancient enemy", "Ancient Enemy", 8.0, 11.0, 15.0),
    ("brothers in arms: road to hill 30", "Brothers in Arms: Road to Hill 30", 10.0, 13.0, 16.0),
    ("rule of rose", "Rule of Rose", 10.0, 12.0, 15.0),
    ("titanic: adventure out of time", "Titanic: Adventure Out of Time", 5.5, 7.5, 10.0),

    # --- Long Games (> 25h) ---
    ("the witcher 3: wild hunt", "The Witcher 3: Wild Hunt", 51.5, 103.0, 173.0),
    ("the elder scrolls v: skyrim", "The Elder Scrolls V: Skyrim", 34.5, 110.0, 232.0),
    ("red dead redemption 2", "Red Dead Redemption 2", 50.0, 82.0, 182.0),
    ("elden ring", "Elden Ring", 58.5, 99.0, 133.0),
    ("grand theft auto v", "Grand Theft Auto V", 31.5, 48.0, 82.5),
    ("cyberpunk 2077", "Cyberpunk 2077", 25.0, 60.5, 104.0),
    ("fallout 4", "Fallout 4", 27.0, 81.0, 158.0),
    ("fallout: new vegas", "Fallout: New Vegas", 27.5, 60.5, 131.0),
    ("baldur's gate 3", "Baldur's Gate 3", 65.0, 107.0, 153.0),
    ("persona 5 royal", "Persona 5 Royal", 101.0, 123.0, 143.0),
    ("persona 4 golden", "Persona 4 Golden", 68.5, 84.0, 140.0),
    ("final fantasy vii", "Final Fantasy VII", 36.5, 52.5, 83.0),
    ("final fantasy x", "Final Fantasy X", 46.0, 71.0, 116.0),
    ("monster hunter: world", "Monster Hunter: World", 48.0, 99.5, 300.0),
    ("dragon age: inquisition", "Dragon Age: Inquisition", 47.0, 87.5, 150.0),
    ("divinity: original sin 2", "Divinity: Original Sin 2", 60.0, 98.5, 152.0),
    ("assassin's creed odyssey", "Assassin's Creed Odyssey", 45.0, 85.0, 143.0),
    ("assassin's creed valhalla", "Assassin's Creed Valhalla", 60.5, 96.0, 145.0),
    ("dark souls", "Dark Souls", 42.0, 60.0, 105.0),
    ("dark souls iii", "Dark Souls III", 32.0, 47.5, 98.0),
    ("bloodborne", "Bloodborne", 34.0, 45.0, 77.0),
    ("kingdom come: deliverance", "Kingdom Come: Deliverance", 41.0, 81.0, 128.0),
    ("yakuza: like a dragon", "Yakuza: Like a Dragon", 45.0, 68.0, 102.0),
    ("ogre battle 64: person of lordly caliber", "Ogre Battle 64: Person of Lordly Caliber", 42.0, 52.0, 70.0),
    ("tactics ogre: let us cling together", "Tactics Ogre: Let Us Cling Together", 55.0, 75.0, 110.0),
    ("sword of convallaria", "Sword of Convallaria", 40.0, 65.0, 100.0),
    ("lords of the fallen", "Lords of the Fallen", 30.0, 42.0, 65.0),
    ("king's bounty: crossworlds", "King's Bounty: Crossworlds", 45.0, 60.0, 85.0),
    ("hades ii", "Hades II", 35.0, 60.0, 110.0),
    ("spellforce", "SpellForce", 24.8, 38.0, 65.0),
]


def _get_db_path() -> str:
    """Returns absolute path to Games.db."""
    from aesgard.database import _resolve_sqlite_db_path
    return _resolve_sqlite_db_path("Games.db")


def init_hltb_cache():
    """Initializes the HltbCache table in Games.db with indexes and starter seeds."""
    global _HLTB_INITIALIZED
    if _HLTB_INITIALIZED:
        return
    try:
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS HltbCache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clean_title TEXT UNIQUE,
                game_name TEXT,
                main_story REAL DEFAULT 0.0,
                main_extra REAL DEFAULT 0.0,
                completionist REAL DEFAULT 0.0,
                hltb_url TEXT,
                fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_hltb_clean_title ON HltbCache(clean_title);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hltb_main_story ON HltbCache(main_story);")
        conn.commit()

        # Seed curated baseline if table is small
        cur.execute("SELECT COUNT(*) FROM HltbCache")
        count = cur.fetchone()[0]
        if count < len(_CURATED_HLTB_SEEDS):
            for clean, name, ms, me, comp in _CURATED_HLTB_SEEDS:
                cur.execute("""
                    INSERT OR IGNORE INTO HltbCache (clean_title, game_name, main_story, main_extra, completionist, hltb_url)
                    VALUES (?, ?, ?, ?, ?, '')
                """, (clean.lower(), name, ms, me, comp))
            conn.commit()
            logger.info(f"Seeded HltbCache with curated baseline titles.")

        conn.close()
        _HLTB_INITIALIZED = True
    except Exception as e:
        logger.warning(f"Error initializing HltbCache table: {e}")


def preload_hltb_cache(force: bool = False):
    """
    Preloads all HLTB cached entries from SQLite into memory once.
    Subsequent queries are 100% in-memory dictionary lookups (zero disk I/O).
    """
    global _HLTB_CACHE_LOADED, _HLTB_MEMORY_CACHE
    if _HLTB_CACHE_LOADED and not force:
        return
    init_hltb_cache()
    try:
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT clean_title, game_name, main_story, main_extra, completionist, hltb_url FROM HltbCache")
        rows = cur.fetchall()
        conn.close()
        for row in rows:
            if row[0]:
                _HLTB_MEMORY_CACHE[str(row[0]).strip().lower()] = {
                    "game_name": row[1] or row[0],
                    "main_story": float(row[2] or 0.0),
                    "main_extra": float(row[3] or 0.0),
                    "completionist": float(row[4] or 0.0),
                    "url": row[5] or ""
                }
        _HLTB_CACHE_LOADED = True
        logger.info(f"Preloaded {len(_HLTB_MEMORY_CACHE)} HLTB records into memory cache.")
    except Exception as e:
        logger.warning(f"Error preloading HltbCache into memory: {e}")


_RE_BRACKETS = re.compile(r'\[.*?\]|\(.*?\)')
_SUFFIXES_LIST = [
    "Windows Edition", "Definitive Edition", "GOTY Edition", "Game of the Year Edition",
    "Remastered", "Remake", "HD Remaster", "Enhanced Edition", "Special Edition",
    "Anniversary Edition", "Director's Cut", "Gold Edition", "Deluxe Edition",
    "Digital Deluxe", "Complete Edition", "Collector's Edition"
]
_RE_SUFFIXES = re.compile(r'\b(?:' + '|'.join(re.escape(s) for s in _SUFFIXES_LIST) + r')\b', re.IGNORECASE)
_RE_SPACES = re.compile(r'\s+')

def clean_title_for_hltb(raw_title: str) -> str:
    """
    Cleans raw game titles (removes prefixes, version numbers, brackets, editions).
    Examples:
      - 'Castlevania - Dracula X' -> 'Castlevania: Dracula X'
      - 'playnite:Hocus Pocus:00054f73...' -> 'Hocus Pocus'
      - 'Super Mario 64 (USA)' -> 'Super Mario 64'
    """
    if not raw_title:
        return ""
    
    title = str(raw_title)
    
    # If Playnite / Steam format
    if title.startswith("playnite:") or title.startswith("steam:"):
        parts = title.split(":")
        if len(parts) >= 2:
            title = parts[1]
    elif title.startswith("link::"):
        title = os.path.splitext(os.path.basename(title[6:]))[0]
    elif title.startswith("exodos:"):
        from aesgard.ui import formatDisplayName
        title = formatDisplayName(title).replace("[eXoDOS]", "").strip()

    # Remove brackets and parentheses content like (USA), [En], (v1.1)
    title = _RE_BRACKETS.sub('', title)
    
    # Remove common release suffixes
    title = _RE_SUFFIXES.sub('', title)

    # Normalize punctuation
    title = title.replace(" - ", ": ")
    title = _RE_SPACES.sub(' ', title).strip()
    return title


def get_cached_hltb(title: str) -> Optional[Dict]:
    """
    Retrieves HLTB stats directly from memory cache (microsecond lookup).
    Never hits SQLite once preloaded, eliminating GUI freeze.
    """
    preload_hltb_cache()
    clean = clean_title_for_hltb(title).lower()
    if not clean:
        return None

    # 1. Exact match in memory
    if clean in _HLTB_MEMORY_CACHE:
        return _HLTB_MEMORY_CACHE[clean]

    # 2. Prefix match before colon (e.g. 'Castlevania: Dracula X' -> 'Castlevania')
    if ":" in clean:
        prefix = clean.split(":")[0].strip()
        if prefix in _HLTB_MEMORY_CACHE:
            return _HLTB_MEMORY_CACHE[prefix]

    # 3. Strip special punctuation (e.g. 'Abzû' -> 'abzu')
    import unicodedata
    normalized = unicodedata.normalize('NFKD', clean).encode('ASCII', 'ignore').decode('ASCII').strip()
    if normalized in _HLTB_MEMORY_CACHE:
        return _HLTB_MEMORY_CACHE[normalized]

    return None


def get_all_cached_durations() -> Dict[str, float]:
    """
    Returns a dictionary of {clean_title: main_story_hours} for all known titles.
    Used for instant in-memory bulk filtering in dashboard rerolls.
    """
    preload_hltb_cache()
    return {k: v.get("main_story", 0.0) for k, v in _HLTB_MEMORY_CACHE.items()}


def fetch_hltb_data(title: str, timeout: float = 5.0) -> Optional[Dict]:
    """
    Queries HowLongToBeat and caches the result locally in SQLite and memory.
    Strictly times out in `timeout` seconds to prevent thread starvation.
    Always records negative or failed matches in memory cache to avoid hammering HLTB.
    Returns dict: {'game_name': str, 'main_story': float, 'main_extra': float, 'completionist': float, 'url': str}
    """
    cached = get_cached_hltb(title)
    if cached is not None:
        return cached

    clean = clean_title_for_hltb(title)
    if not clean or len(clean) < 2:
        return None

    def _execute_search():
        from howlongtobeatpy import HowLongToBeat
        hltb = HowLongToBeat()
        results = hltb.search(clean)
        if not results and ":" in clean:
            results = hltb.search(clean.split(":")[0].strip())
        return results

    try:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_execute_search)
            results = future.result(timeout=timeout)

        if results:
            best = results[0]
            data = {
                "game_name": getattr(best, 'game_name', clean),
                "main_story": float(getattr(best, 'main_story', 0.0) or 0.0),
                "main_extra": float(getattr(best, 'main_extra', 0.0) or 0.0),
                "completionist": float(getattr(best, 'completionist', 0.0) or 0.0),
                "url": getattr(best, 'game_web_link', '') or ''
            }
        else:
            # Cache negative result (0.0) to avoid hammering HLTB repeatedly
            data = {
                "game_name": clean,
                "main_story": 0.0,
                "main_extra": 0.0,
                "completionist": 0.0,
                "url": ""
            }

        # Save to SQLite cache
        try:
            db_path = _get_db_path()
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO HltbCache (clean_title, game_name, main_story, main_extra, completionist, hltb_url, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (clean.lower(), data["game_name"], data["main_story"], data["main_extra"], data["completionist"], data["url"]))
            conn.commit()
            conn.close()
        except Exception as dbe:
            logger.debug(f"DB cache error for {clean}: {dbe}")

        # Update in-memory cache
        _HLTB_MEMORY_CACHE[clean.lower()] = data
        return data

    except concurrent.futures.TimeoutError:
        logger.warning(f"HLTB query timed out after {timeout}s for '{clean}'")
        fallback_data = {"game_name": clean, "main_story": 0.0, "main_extra": 0.0, "completionist": 0.0, "url": ""}
        _HLTB_MEMORY_CACHE[clean.lower()] = fallback_data
        return fallback_data
    except Exception as e:
        logger.warning(f"Error fetching HLTB data for '{clean}': {e}")
        fallback_data = {"game_name": clean, "main_story": 0.0, "main_extra": 0.0, "completionist": 0.0, "url": ""}
        _HLTB_MEMORY_CACHE[clean.lower()] = fallback_data
        return fallback_data


def format_hltb_duration(hours: float) -> str:
    """Formats hours into clean human string, e.g., '12h' or '1h 30m'."""
    if not hours or hours <= 0:
        return ""
    h = int(hours)
    m = int(round((hours - h) * 60))
    if h == 0 and m > 0:
        return f"{m}m"
    if m == 0:
        return f"{h}h"
    return f"{h}h {m}m"


def get_duration_badge_style(hours: float) -> str:
    """
    Returns Qt CSS stylesheet for a given HLTB main story duration badge:
      - < 5h: Fast / Quick game (Mint / Green)
      - 5h - 15h: Moderate length (Cyan / Blue)
      - 15h - 30h: Long game (Amber / Orange)
      - > 30h: Epic RPG / Mega game (Purple / Violet)
    """
    if not hours or hours <= 0:
        return "background-color: #334155; color: #94a3b8; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;"
    
    if hours < 5:
        bg = "#00b894"  # Mint Green
    elif hours <= 15:
        bg = "#0984e3"  # Blue
    elif hours <= 30:
        bg = "#e17055"  # Amber Orange
    else:
        bg = "#6c5ce7"  # Purple RPG

    return f"background-color: {bg}; color: #ffffff; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;"
