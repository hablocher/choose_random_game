# -*- coding: utf-8 -*-
"""
SQLite Live History database manager for Canino Gaming.
"""
import os
import sqlite3
import logging
import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)


class LiveHistoryManager:
    """Manages the history of games played during YouTube live streams in SQLite."""

    def __init__(self, dbPath: str = "Games.db"):
        if not os.path.isabs(dbPath):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            dbPath = os.path.join(base_dir, dbPath)
        self.dbPath = dbPath
        self._initDb()

    def _initDb(self):
        try:
            conn = sqlite3.connect(self.dbPath)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS LiveHistory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stream_date TEXT,
                    game_name TEXT,
                    duration_hours REAL DEFAULT 0.0,
                    notes TEXT,
                    youtube_url TEXT
                );
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Error initializing LiveHistory table: {e}")

    def recordLive(self, gameName: str, notes: str = "", durationHours: float = 2.0, youtubeUrl: str = "") -> int:
        """Records a completed or current live stream session."""
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            conn = sqlite3.connect(self.dbPath)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO LiveHistory (stream_date, game_name, duration_hours, notes, youtube_url)
                VALUES (?, ?, ?, ?, ?)
            """, (now_str, gameName, durationHours, notes, youtubeUrl))
            new_id = cur.lastrowid
            conn.commit()
            conn.close()
            logger.info(f"Recorded live stream for game: {gameName} (id={new_id})")
            return new_id
        except Exception as e:
            logger.warning(f"Error recording live stream: {e}")
            return -1

    def getLiveHistory(self, limit: int = 50) -> List[Dict]:
        """Retrieves recent live stream entries sorted descending by date."""
        try:
            conn = sqlite3.connect(self.dbPath)
            cur = conn.cursor()
            cur.execute("""
                SELECT id, stream_date, game_name, duration_hours, notes, youtube_url
                FROM LiveHistory ORDER BY id DESC LIMIT ?
            """, (limit,))
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "id": r[0],
                    "date": r[1],
                    "gameName": r[2],
                    "duration": r[3],
                    "notes": r[4],
                    "youtubeUrl": r[5]
                }
                for r in rows
            ]
        except Exception as e:
            logger.warning(f"Error reading LiveHistory: {e}")
            return []

    def deleteLive(self, liveId: int) -> bool:
        """Deletes a live history record."""
        try:
            conn = sqlite3.connect(self.dbPath)
            cur = conn.cursor()
            cur.execute("DELETE FROM LiveHistory WHERE id = ?", (liveId,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.warning(f"Error deleting live history id {liveId}: {e}")
            return False
