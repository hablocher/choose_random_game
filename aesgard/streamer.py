# -*- coding: utf-8 -*-
"""
Streamer & Live Assistant Module for Choose Random Game.
Provides:
- SQLite Live History database manager
- Streamer Overlay Window for OBS Studio capture (Frameless with Dark / Chroma Green / Magenta modes)
"""
import os
import sqlite3
import logging
import datetime
from typing import List, Dict, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap, QImage, QColor

logger = logging.getLogger(__name__)

class LiveHistoryManager:
    """Manages the history of games played during YouTube live streams in SQLite."""

    def __init__(self, dbPath: str = "Games.db"):
        if not os.path.isabs(dbPath):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

class StreamerOverlayWindow(QWidget):
    """
    Frameless, clean overlay window designed for OBS Studio Window Capture.
    Supports:
    - Sleek Dark Gamer style
    - Chroma Key Green (#00FF00) for transparency cutout
    - Chroma Key Magenta (#FF00FF)
    """

    STYLES = {
        "dark": {
            "windowBg": "#0d0f14",
            "cardBg": "#161b26",
            "border": "#00cec9",
            "titleColor": "#ffffff",
            "subColor": "#cbd5e1",
            "badgeBg": "#e17055",
            "badgeText": "#ffffff"
        },
        "green": {
            "windowBg": "#00ff00",
            "cardBg": "#161b26",
            "border": "#00cec9",
            "titleColor": "#ffffff",
            "subColor": "#cbd5e1",
            "badgeBg": "#e17055",
            "badgeText": "#ffffff"
        },
        "magenta": {
            "windowBg": "#ff00ff",
            "cardBg": "#161b26",
            "border": "#00cec9",
            "titleColor": "#ffffff",
            "subColor": "#cbd5e1",
            "badgeBg": "#e17055",
            "badgeText": "#ffffff"
        }
    }

    def __init__(self, gameTitle: str = "Aguardando Sorteio...", coverPixmap: Optional[QPixmap] = None, platformText: str = "PC / LIVE"):
        super().__init__()
        self.currentMode = "dark"
        self.gameTitle = gameTitle
        self.coverPixmap = coverPixmap
        self.platformText = platformText

        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.resize(560, 220)
        self.initUI()

    def initUI(self):
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(10, 10, 10, 10)

        # Card container
        self.card = QFrame()
        self.cardLayout = QHBoxLayout(self.card)
        self.cardLayout.setContentsMargins(16, 16, 16, 16)
        self.cardLayout.setSpacing(18)

        # Cover Image
        self.coverLabel = QLabel()
        self.coverLabel.setFixedSize(140, 160)
        self.coverLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.coverLabel.setStyleSheet("border-radius: 8px; background-color: #000000;")
        if self.coverPixmap:
            self.coverLabel.setPixmap(self.coverPixmap.scaled(140, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.cardLayout.addWidget(self.coverLabel)

        # Info Column
        infoCol = QVBoxLayout()
        infoCol.setSpacing(6)

        # Top row badges
        badgeRow = QHBoxLayout()
        self.liveBadge = QLabel("🔴 AO VIVO NO YOUTUBE")
        self.liveBadge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        badgeRow.addWidget(self.liveBadge)

        self.platformBadge = QLabel(self.platformText.upper())
        self.platformBadge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.platformBadge.setStyleSheet("background-color: #2d3436; color: #dfe6e9; border-radius: 4px; padding: 2px 8px;")
        badgeRow.addWidget(self.platformBadge)
        badgeRow.addStretch()

        # Theme toggle buttons
        btnChroma = QPushButton("🎨 Chroma")
        btnChroma.setFixedSize(65, 22)
        btnChroma.setCursor(Qt.CursorShape.PointingHandCursor)
        btnChroma.setStyleSheet("background-color: #242b3b; color: #a0aec0; border: none; border-radius: 4px; font-size: 10px;")
        btnChroma.clicked.connect(self.cycleChromaMode)
        badgeRow.addWidget(btnChroma)

        btnClose = QPushButton("✕")
        btnClose.setFixedSize(24, 22)
        btnClose.setCursor(Qt.CursorShape.PointingHandCursor)
        btnClose.setStyleSheet("background-color: #242b3b; color: #ff7675; border: none; border-radius: 4px; font-weight: bold;")
        btnClose.clicked.connect(self.close)
        badgeRow.addWidget(btnClose)

        infoCol.addLayout(badgeRow)

        # Title
        self.titleLabel = QLabel(self.gameTitle)
        self.titleLabel.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.titleLabel.setWordWrap(True)
        infoCol.addWidget(self.titleLabel)

        # Subtitle
        self.subLabel = QLabel("🎮 Jogo sorteado ao vivo • Pronto para rodar!")
        self.subLabel.setFont(QFont("Segoe UI", 10))
        infoCol.addWidget(self.subLabel)
        infoCol.addStretch()

        self.cardLayout.addLayout(infoCol)
        self.mainLayout.addWidget(self.card)

        self.applyStyle()

    def applyStyle(self):
        st = self.STYLES[self.currentMode]
        self.setStyleSheet(f"background-color: {st['windowBg']};")
        self.card.setStyleSheet(
            f"background-color: {st['cardBg']}; "
            f"border: 2px solid {st['border']}; "
            f"border-radius: 12px;"
        )
        self.titleLabel.setStyleSheet(f"color: {st['titleColor']};")
        self.subLabel.setStyleSheet(f"color: {st['subColor']};")
        self.liveBadge.setStyleSheet(
            f"background-color: {st['badgeBg']}; color: {st['badgeText']}; "
            f"border-radius: 4px; padding: 2px 8px;"
        )

    def cycleChromaMode(self):
        modes = ["dark", "green", "magenta"]
        idx = (modes.index(self.currentMode) + 1) % len(modes)
        self.currentMode = modes[idx]
        self.applyStyle()

    def updateGame(self, title: str, pixmap: Optional[QPixmap], platform: str = "PC / LIVE"):
        self.gameTitle = title
        self.titleLabel.setText(title)
        self.platformText = platform
        self.platformBadge.setText(platform.upper())
        if pixmap:
            self.coverLabel.setPixmap(pixmap.scaled(140, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    # Allow dragging frameless window
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
