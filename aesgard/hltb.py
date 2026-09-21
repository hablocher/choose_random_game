# -*- coding: utf-8 -*-
"""
HowLongToBeat (HLTB) integration module for Choose Random Game.
Fetches estimated completion times using howlongtobeatpy, with local SQLite caching
and resilient title cleaning.
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

def _get_db_path() -> str:
    """Returns absolute path to Games.db."""
    from aesgard.database import _resolve_sqlite_db_path
    return _resolve_sqlite_db_path("Games.db")

def init_hltb_cache():
    """Initializes the HltbCache table in Games.db with performance indexes."""
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
        conn.close()
        _HLTB_INITIALIZED = True
    except Exception as e:
        logger.warning(f"Error initializing HltbCache table: {e}")

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
    title = re.sub(r'\[.*?\]', '', title)
    title = re.sub(r'\(.*?\)', '', title)
    
    # Remove common release suffixes
    suffixes = [
        "Windows Edition", "Definitive Edition", "GOTY Edition", "Game of the Year Edition",
        "Remastered", "Remake", "HD Remaster", "Enhanced Edition", "Special Edition",
        "Anniversary Edition", "Director's Cut", "Gold Edition", "Deluxe Edition"
    ]
    for s in suffixes:
        pattern = re.compile(rf'\b{re.escape(s)}\b', re.IGNORECASE)
        title = pattern.sub('', title)

    # Normalize punctuation
    title = title.replace(" - ", ": ")
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def get_cached_hltb(title: str) -> Optional[Dict]:
    """Retrieves HLTB stats from memory or SQLite cache if available."""
    init_hltb_cache()
    clean = clean_title_for_hltb(title).lower()
    if not clean:
        return None

    # 1. Memory check
    if clean in _HLTB_MEMORY_CACHE:
        return _HLTB_MEMORY_CACHE[clean]

    # 2. SQLite check
    try:
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT game_name, main_story, main_extra, completionist, hltb_url FROM HltbCache WHERE clean_title = ?",
            (clean,)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            data = {
                "game_name": row[0],
                "main_story": row[1],
                "main_extra": row[2],
                "completionist": row[3],
                "url": row[4]
            }
            _HLTB_MEMORY_CACHE[clean] = data
            return data
    except Exception as e:
        logger.warning(f"Error querying HltbCache for '{clean}': {e}")

    return None

def fetch_hltb_data(title: str, max_retries: int = 1) -> Optional[Dict]:
    """
    Queries HowLongToBeat and caches the result locally in SQLite.
    Returns dict: {'game_name': str, 'main_story': float, 'main_extra': float, 'completionist': float, 'url': str}
    """
    cached = get_cached_hltb(title)
    if cached is not None:
        return cached

    clean = clean_title_for_hltb(title)
    if not clean or len(clean) < 2:
        return None

    data = None
    try:
        from howlongtobeatpy import HowLongToBeat
        hltb = HowLongToBeat()
        results = hltb.search(clean)
        if not results and ":" in clean:
            # Try searching just the main prefix before the colon
            results = hltb.search(clean.split(":")[0].strip())

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
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO HltbCache (clean_title, game_name, main_story, main_extra, completionist, hltb_url, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (clean.lower(), data["game_name"], data["main_story"], data["main_extra"], data["completionist"], data["url"]))
        conn.commit()
        conn.close()

        _HLTB_MEMORY_CACHE[clean.lower()] = data
        return data

    except Exception as e:
        logger.warning(f"Error fetching HLTB data for '{clean}': {e}")
        return None

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

def get_duration_badge_style(hours: float) -> Tuple[str, str]:
    """
    Returns (badge_text, background_color) for a given HLTB main story duration:
      - < 5h: Fast / Quick game (Mint / Green)
      - 5h - 15h: Moderate length (Cyan / Blue)
      - 15h - 30h: Long game (Amber / Orange)
      - > 30h: Epic RPG / Mega game (Purple / Violet)
    """
    if not hours or hours <= 0:
        return "", ""
    
    text = f"⏱️ ~{format_hltb_duration(hours)} (HLTB)"
    if hours < 5:
        return text, "#00b894"  # Mint Green
    elif hours <= 15:
        return text, "#0984e3"  # Blue
    elif hours <= 30:
        return text, "#e17055"  # Amber Orange
    else:
        return text, "#6c5ce7"  # Purple RPG
