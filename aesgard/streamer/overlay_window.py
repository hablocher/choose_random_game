# -*- coding: utf-8 -*-
"""
Streamer Overlay Window for OBS Studio capture (Frameless with Dark / Chroma Green / Magenta modes).
"""
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap


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
            "windowBg": "#070d14",
            "cardBg": "#0c1522",
            "border": "#38bdf8",
            "titleColor": "#f0f6fc",
            "subColor": "#7dd3fc",
            "badgeBg": "#0284c7",
            "badgeText": "#ffffff"
        },
        "green": {
            "windowBg": "#00ff00",
            "cardBg": "#0c1522",
            "border": "#38bdf8",
            "titleColor": "#f0f6fc",
            "subColor": "#7dd3fc",
            "badgeBg": "#0284c7",
            "badgeText": "#ffffff"
        },
        "magenta": {
            "windowBg": "#ff00ff",
            "cardBg": "#0c1522",
            "border": "#38bdf8",
            "titleColor": "#f0f6fc",
            "subColor": "#7dd3fc",
            "badgeBg": "#0284c7",
            "badgeText": "#ffffff"
        }
    }

    def __init__(self, gameTitle: str = "Aguardando Sorteio...", coverPixmap: Optional[QPixmap] = None, platformText: str = "PC / LIVE"):
        super().__init__()
        self.setWindowTitle("Canino Gaming - OBS Overlay")
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
        self.subLabel = QLabel("🐺 Jogo sorteado pelo Canino Gaming • Pronto para rodar!")
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

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
