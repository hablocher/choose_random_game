# -*- coding: utf-8 -*-
"""
Theme components and utilities for Caninos Brancos / White Fang aesthetic.
"""
from typing import Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPixmap, QLinearGradient

BACKGROUND_PRESETS = [
    {
        "id": "lpm_pocket",
        "title": "🐺 Edição L&PM Pocket (Capa Oficial)",
        "path": "assets/backgrounds/caninos_brancos_lpm.png",
        "default_opacity": 0.22,
        "description": "Capa oficial com o lobo uivando na floresta de pinheiros e neve do Yukon."
    },
    {
        "id": "boreal_aurora",
        "title": "🌌 Aurora Boreal do Yukon (Edição Ártica)",
        "path": "assets/backgrounds/white_fang_boreal_aurora.jpg",
        "default_opacity": 0.20,
        "description": "Lobo selvagem sob o céu com aurora boreal verde esmeralda e montanhas geladas."
    },
    {
        "id": "classic_1906",
        "title": "📜 Edição Clássica Macmillan 1906 (Trilha de Neve)",
        "path": "assets/backgrounds/white_fang_classic_1906.jpg",
        "default_opacity": 0.18,
        "description": "Ilustração vintage da primeira edição histórica de Jack London em Klondike."
    },
    {
        "id": "dark_pure",
        "title": "⬛ Fundo Escuro Puro (Sem Imagem)",
        "path": "",
        "default_opacity": 0.0,
        "description": "Fundo minimalista escuro focado puramente nos dados e nas cartas."
    }
]


def extractChannelHandle(url: str, default: str = "") -> str:
    """Extracts @handle or channel name from YouTube URL."""
    if not url:
        return default
    clean = url.rstrip('/')
    if '@' in clean:
        return '@' + clean.split('@')[-1]
    part = clean.split('/')[-1]
    return part if part else default


class ThemedCentralWidget(QWidget):
    """
    Central widget for Caninos Brancos / White Fang theme.
    Renders background book art with smooth aspect-ratio scaling, customizable opacity,
    and an atmospheric vignette gradient overlay for high contrast and readability.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bgPixmap: Optional[QPixmap] = None
        self.bgOpacity: float = 0.22

    def setBackground(self, pixmap: Optional[QPixmap], opacity: float):
        self.bgPixmap = pixmap
        self.bgOpacity = max(0.0, min(1.0, float(opacity)))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 1. Base deep Yukon night background
        painter.fillRect(self.rect(), QColor("#070d14"))

        # 2. Draw background image if set
        if self.bgPixmap and not self.bgPixmap.isNull() and self.bgOpacity > 0.001:
            scaled = self.bgPixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.setOpacity(self.bgOpacity)
            painter.drawPixmap(x, y, scaled)

            # 3. Vignette & contrast overlay
            painter.setOpacity(1.0)
            grad = QLinearGradient(0, 0, 0, self.height())
            grad.setColorAt(0.0, QColor(7, 13, 20, 205))
            grad.setColorAt(0.28, QColor(7, 13, 20, 140))
            grad.setColorAt(0.72, QColor(7, 13, 20, 160))
            grad.setColorAt(1.0, QColor(7, 13, 20, 235))
            painter.fillRect(self.rect(), grad)
