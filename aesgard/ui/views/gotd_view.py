# -*- coding: utf-8 -*-
"""
Game of the Day (Jogo do Dia) View Component for Canino Gaming.
Presents a daily spotlight from installed backlog games with rich art, stats, and direct launch.
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QImage

from aesgard.gameutil import (
    executeGame, installGame, findGameIcon, getGameOfTheDay
)
from aesgard.database import findGameInfo
from aesgard.ui import formatDisplayName, detectPlatform, getPlatformColor
from aesgard.intel_dialog import GameIntelDialog
from aesgard.sound import get_sound_manager

logger = logging.getLogger(__name__)


class GotdView(QWidget):
    """View container for Jogo do Dia (Instinto Selvagem)."""
    def __init__(self, dashboard, parent=None):
        super().__init__(parent)
        self.dashboard = dashboard
        self.currentGotd = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("GotdCard")
        card.setFixedWidth(640)
        cardLayout = QVBoxLayout(card)
        cardLayout.setContentsMargins(30, 24, 30, 24)
        cardLayout.setSpacing(14)

        # Header tag
        tagRow = QHBoxLayout()
        tagLabel = QLabel("❄️ INSTINTO SELVAGEM • RECOMENDAÇÃO DO DIA (INSTALADO NO PC)")
        tagLabel.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        tagLabel.setStyleSheet("color: #38bdf8; letter-spacing: 1px;")
        tagRow.addWidget(tagLabel)
        tagRow.addStretch()

        self.gotdPlatformBadge = QLabel("LOCAL")
        self.gotdPlatformBadge.setObjectName("PlatformBadge")
        tagRow.addWidget(self.gotdPlatformBadge)
        cardLayout.addLayout(tagRow)

        # Image cover
        imgFrame = QFrame()
        imgFrame.setStyleSheet("background-color: #080d14; border: 1px solid #1c2f44; border-radius: 12px;")
        imgLayout = QVBoxLayout(imgFrame)
        imgLayout.setContentsMargins(8, 8, 8, 8)

        self.gotdImageLabel = QLabel()
        self.gotdImageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gotdImageLabel.setFixedSize(180, 180)
        imgLayout.addWidget(self.gotdImageLabel, 0, Qt.AlignmentFlag.AlignCenter)
        cardLayout.addWidget(imgFrame, 0, Qt.AlignmentFlag.AlignCenter)

        # Title
        self.gotdTitleLabel = QLabel("Título do Jogo do Dia")
        self.gotdTitleLabel.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.gotdTitleLabel.setStyleSheet("color: #ffffff;")
        self.gotdTitleLabel.setWordWrap(True)
        self.gotdTitleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cardLayout.addWidget(self.gotdTitleLabel)

        # Stats
        self.gotdStatsLabel = QLabel("Vezes jogado: 0 • Status: Em aberto")
        self.gotdStatsLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gotdStatsLabel.setStyleSheet("color: #a0aec0; font-size: 13px;")
        cardLayout.addWidget(self.gotdStatsLabel)

        cardLayout.addSpacing(10)

        # Big Play Button
        self.btnGotdPlay = QPushButton("▶  CAÇAR JOGO DO DIA AGORA")
        self.btnGotdPlay.setObjectName("BtnPlay")
        self.btnGotdPlay.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnGotdPlay.clicked.connect(self.onPlayGotd)
        cardLayout.addWidget(self.btnGotdPlay)

        # Reroll Button
        self.btnGotdReroll = QPushButton("🎲  SORTEAR OUTRA RECOMENDAÇÃO SELVAGEM")
        self.btnGotdReroll.setObjectName("BtnReroll")
        self.btnGotdReroll.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnGotdReroll.clicked.connect(lambda: self.onRerollGotd(initial=False))
        cardLayout.addWidget(self.btnGotdReroll)

        # Intel & Guides Button
        self.btnGotdIntel = QPushButton("ℹ️  Guia, Detonados & Dicas deste Jogo")
        self.btnGotdIntel.setObjectName("BtnSecondary")
        self.btnGotdIntel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnGotdIntel.clicked.connect(self.onOpenGotdIntel)
        cardLayout.addWidget(self.btnGotdIntel)

        layout.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)

    def onRerollGotd(self, initial=False):
        if not initial:
            get_sound_manager().play("wolf_growl")
        content = getattr(self.dashboard, 'content', [])
        chosen = getGameOfTheDay(content, seed_date=initial)
        if not chosen:
            chosen = getattr(self.dashboard, 'currentChoice', None)
        self.currentGotd = chosen
        if hasattr(self.dashboard, 'currentGotd'):
            self.dashboard.currentGotd = chosen
        self.updateGotdDisplay(chosen)

    def updateGotdDisplay(self, gameEntry):
        if not gameEntry:
            return
        display_name = formatDisplayName(gameEntry)
        self.gotdTitleLabel.setText(display_name)

        platform = detectPlatform(gameEntry)
        self.gotdPlatformBadge.setText(platform.upper())
        self.gotdPlatformBadge.setStyleSheet(
            f"background-color: {getPlatformColor(platform)}; color: #ffffff; "
            f"border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;"
        )

        info = findGameInfo(gameEntry)
        times_played = info[2] if info else 0
        finished = info[4] if info else 0
        installed = info[6] if (info and len(info) >= 7) else 1
        is_installed = bool(installed)

        status_text = "Zerado ✔" if finished else "Em aberto"
        inst_text = "Pronto para rodar" if is_installed else "Não instalado"
        self.gotdStatsLabel.setText(f"Vezes jogado: {times_played}x • Status: {status_text} • {inst_text}")

        if is_installed:
            self.btnGotdPlay.setText("▶  CAÇAR JOGO DO DIA AGORA")
            self.btnGotdPlay.setStyleSheet("")
        else:
            self.btnGotdPlay.setText("📥  INSTALAR JOGO DO DIA")
            self.btnGotdPlay.setStyleSheet("""
                QPushButton#BtnPlay {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6c5ce7, stop:1 #a29bfe);
                    color: #ffffff;
                    font-size: 14px;
                    font-weight: bold;
                    border: none;
                    border-radius: 8px;
                    padding: 12px;
                }
            """)

        try:
            cfg = getattr(self.dashboard, 'config', None)
            pn_path = getattr(cfg, 'playnitePath', '') if cfg else ''
            pilImg = findGameIcon(gameEntry, playnitePath=pn_path)
            pilImg = pilImg.convert("RGBA")
            data = pilImg.tobytes("raw", "RGBA")
            qim = QImage(data, pilImg.size[0], pilImg.size[1], QImage.Format.Format_RGBA8888)
            pix = QPixmap.fromImage(qim).scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.gotdImageLabel.setPixmap(pix)
        except Exception as e:
            logger.warning(f"Error rendering GOTD icon: {e}")

    def onPlayGotd(self):
        target = self.currentGotd or getattr(self.dashboard, 'currentChoice', None)
        if not target:
            return
        info = findGameInfo(target)
        is_installed = (info[6] == 1) if (info and len(info) >= 7) else 1

        if is_installed:
            logger.info(f"Launching Game of the Day: {target}")
            if hasattr(self.dashboard, 'startGameplaySession'):
                self.dashboard.startGameplaySession(target)
            self.dashboard.showMinimized()
            executeGame(target, getattr(self.dashboard, 'steamOwnedGames', []))
        else:
            logger.info(f"Installing Game of the Day: {target}")
            success = installGame(target)
            if success:
                QMessageBox.information(self, "Instalação", f"Comando de instalação acionado para:\n{formatDisplayName(target)}")
            else:
                QMessageBox.warning(self, "Instalação", f"Não foi possível disparar instalador automaticamente para:\n{formatDisplayName(target)}")

        if hasattr(self.dashboard, 'refreshStats'):
            self.dashboard.refreshStats()
        if hasattr(self.dashboard, 'refreshTable'):
            self.dashboard.refreshTable()
        if self.currentGotd:
            self.updateGotdDisplay(self.currentGotd)

    def onOpenGotdIntel(self):
        target = self.currentGotd or getattr(self.dashboard, 'currentChoice', None)
        if not target:
            return
        pix = self.gotdImageLabel.pixmap()
        dlg = GameIntelDialog(target, coverPixmap=pix, parent=self)
        dlg.exec()
