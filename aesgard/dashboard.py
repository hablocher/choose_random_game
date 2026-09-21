# -*- coding: utf-8 -*-
"""
Modern Gaming Dashboard for Choose Random Game using PyQt6.
Features:
- Real-time library statistics (total games, sessions, backlog progress, favorites)
- Hero section for random game picker with instant Reroll and category filtering
- Interactive database explorer with instant search and status filtering
- 'Game of the Day' (Jogo do Dia) strictly from installed games
- 'GOTY (Game of the Year)' randomizer & historical Hall of Fame browser
- Direct launch from database list, hero card, Game of the Day, or GOTY
- Dark mode gaming aesthetics with sleek styling
"""
import os
import sys
import logging
import random
import webbrowser
from PIL import Image

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QSplitter, QMessageBox,
    QStackedWidget, QButtonGroup, QProgressDialog, QCheckBox, QGridLayout
)
from PyQt6.QtCore import Qt, QSize, QTimer, QRectF
from PyQt6.QtGui import QFont, QPixmap, QImage, QColor, QIcon, QPainter, QPen, QBrush

from aesgard.gameutil import (
    executeGame, installGame, scanAllSources, findGameIcon, chooseGame,
    getGameOfTheDay, linkPrefix, exodosPrefix
)
from aesgard.playnite import PLAYNITE_PREFIX
from aesgard.database import (
    getDatabaseStats, getGamesList, setFinished, setFavorite,
    findGameInfo, getRandomGoty, getAllGotys, importContentToDatabase,
    getInstalledGamesSet, getUninstalledGamesSet, getFavoriteGamesSet, getPlayedGamesSet
)
from aesgard.ui import formatDisplayName, detectPlatform, getPlatformColor, clearPlayniteMetaCache
from aesgard.intel_dialog import GameIntelDialog
from aesgard.streamer import LiveHistoryManager, StreamerOverlayWindow
from aesgard.hltb import (
    get_cached_hltb, fetch_hltb_data, format_hltb_duration, get_duration_badge_style,
    clean_title_for_hltb, get_all_cached_durations, preload_hltb_cache
)
from aesgard.web_overlay import (
    start_overlay_server, update_overlay_game, update_overlay_timer, 
    update_overlay_channel, update_overlay_poll, record_poll_vote
)
from aesgard.wheel_dialog import WheelOfFortuneDialog
from aesgard.card_generator import generate_live_card
import subprocess
import time

logger = logging.getLogger(__name__)

# Dark Mode Modern QSS
STYLESHEET = """
QMainWindow {
    background-color: #0d0f14;
}

QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    color: #e2e8f0;
}

/* Header & Stat Cards */
QFrame#StatCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1e29, stop:1 #131722);
    border: 1px solid #2a3142;
    border-radius: 10px;
    padding: 6px 8px;
}

QLabel#StatValue {
    font-size: 20px;
    font-weight: bold;
    color: #00cec9;
}

QLabel#StatLabel {
    font-size: 10px;
    color: #8c96a8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Nav Tabs */
QPushButton.NavBtn {
    background-color: #161a24;
    border: 1px solid #2b3244;
    border-radius: 8px;
    color: #a0aec0;
    font-size: 12px;
    font-weight: bold;
    padding: 7px 12px;
}
QPushButton.NavBtn:hover {
    background-color: #1f2533;
    color: #ffffff;
    border-color: #3e4a63;
}
QPushButton.NavBtn:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0984e3, stop:1 #6c5ce7);
    color: #ffffff;
    border-color: #6c5ce7;
}

/* Hero Section */
QFrame#HeroCard {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #181c26, stop:1 #12151d);
    border: 1px solid #2b3244;
    border-radius: 14px;
    padding: 18px;
}

/* Game of the Day Card */
QFrame#GotdCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a2233, stop:1 #111520);
    border: 1px solid #00cec9;
    border-radius: 16px;
    padding: 24px;
}

/* GOTY Card (Golden) */
QFrame#GotyCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2c2214, stop:1 #16120d);
    border: 1px solid #d4af37;
    border-radius: 16px;
    padding: 24px;
}

QLabel#GameTitle {
    font-size: 18px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#PlatformBadge {
    background-color: #2d3748;
    color: #a0aec0;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: bold;
}

/* Buttons */
QPushButton#BtnPlay {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00b894, stop:1 #00cec9);
    color: #0d0f14;
    font-size: 14px;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 12px 20px;
}
QPushButton#BtnPlay:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00c9a0, stop:1 #10dfda);
}
QPushButton#BtnPlay:pressed {
    background: #00a885;
}

QPushButton#BtnReroll {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0984e3, stop:1 #6c5ce7);
    color: #ffffff;
    font-size: 13px;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
}
QPushButton#BtnReroll:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a92ec, stop:1 #7d6ef0);
}

QPushButton#BtnGoty {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d4af37, stop:1 #f39c12);
    color: #12100a;
    font-size: 14px;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 12px 22px;
}
QPushButton#BtnGoty:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e5c158, stop:1 #f1c40f);
}

QPushButton#BtnSecondary {
    background-color: #222734;
    border: 1px solid #323b4f;
    color: #cbd5e1;
    font-size: 12px;
    border-radius: 6px;
    padding: 6px 12px;
}
QPushButton#BtnSecondary:hover {
    background-color: #2a3142;
    border-color: #4a5568;
    color: #ffffff;
}

/* Inputs & Combos */
QLineEdit {
    background-color: #161a24;
    border: 1px solid #2b3244;
    border-radius: 8px;
    padding: 8px 12px;
    color: #ffffff;
    font-size: 13px;
}
QLineEdit:focus {
    border-color: #0984e3;
}

QComboBox {
    background-color: #161a24;
    border: 1px solid #2b3244;
    border-radius: 6px;
    padding: 6px 12px;
    color: #cbd5e1;
    font-size: 12px;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #1a1e29;
    border: 1px solid #2a3142;
    selection-background-color: #0984e3;
    color: #ffffff;
}

/* Table Widget */
QTableWidget {
    background-color: #131720;
    border: 1px solid #242b3b;
    border-radius: 8px;
    gridline-color: #1e2433;
    font-size: 12px;
}
QTableWidget::item {
    padding: 6px;
    border-bottom: 1px solid #1a202d;
}
QTableWidget::item:selected {
    background-color: #1e3a5f;
    color: #ffffff;
}
QHeaderView::section {
    background-color: #181d28;
    color: #8c96a8;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #2a3142;
    font-weight: bold;
    font-size: 11px;
    text-transform: uppercase;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #11131a;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #2b3244;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Dialogs & MessageBoxes (Dark Mode Contrast) */
QDialog, QMessageBox, QProgressDialog {
    background-color: #12151d;
    color: #e2e8f0;
}
QMessageBox QLabel, QProgressDialog QLabel {
    color: #e2e8f0;
    font-size: 13px;
    background-color: transparent;
}
QMessageBox QPushButton, QProgressDialog QPushButton {
    background-color: #222734;
    border: 1px solid #323b4f;
    color: #ffffff;
    font-size: 12px;
    font-weight: bold;
    border-radius: 6px;
    padding: 6px 18px;
    min-width: 80px;
}
QMessageBox QPushButton:hover, QProgressDialog QPushButton:hover {
    background-color: #2a3142;
    border-color: #0984e3;
    color: #ffffff;
}
QMessageBox QPushButton:pressed, QProgressDialog QPushButton:pressed {
    background-color: #1a1e29;
}

QProgressBar {
    background-color: #161a24;
    border: 1px solid #2b3244;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00b894, stop:1 #00cec9);
    border-radius: 5px;
}
"""


def extractChannelHandle(url: str, default: str = "") -> str:
    """Extracts @handle or channel name from YouTube URL."""
    if not url:
        return default
    clean = url.rstrip('/')
    if '@' in clean:
        return '@' + clean.split('@')[-1]
    part = clean.split('/')[-1]
    return part if part else default


class GamingDashboard(QMainWindow):
    def __init__(self, content, initialChoice, steamOwnedGames, config):
        super().__init__()
        # Store configuration right at the beginning
        self.config = config
        self.content = content
        self.currentChoice = initialChoice
        self.steamOwnedGames = steamOwnedGames
        self.currentGotd = None
        self.currentGoty = None
        self.liveHistoryMgr = LiveHistoryManager(dbPath=getattr(self.config, 'DatabaseName', 'Games.db'))
        self.overlayWindow = None
        self._rouletteTimer = None
        self.chatChoiceTrio = []
        self.chatVotes = [0, 0, 0]

        # New Features State: Web Overlay, Session Timer, Mystery Mode
        self.sessionStartTime = None
        self.activePlayingGame = None
        self.sessionTimer = QTimer(self)
        self.sessionTimer.setInterval(1000)
        self.sessionTimer.timeout.connect(self._onSessionTimerTick)

        self.isMysteryMode = False
        self.mysteryRevealed = False

        # Start Web Overlay Server (port 8089)
        try:
            self.overlayServerStarted = start_overlay_server(port=8089)
            liveChannelUrl = getattr(self.config, 'streamerYouTubeLiveChannel', '').strip()
            mainChannelUrl = getattr(self.config, 'streamerYouTubeMainChannel', '').strip()
            handle = extractChannelHandle(liveChannelUrl or mainChannelUrl, "@Hablocher")
            update_overlay_channel(handle)
        except Exception as e:
            logger.warning(f"Não foi possível iniciar servidor de overlay web: {e}")
            self.overlayServerStarted = False

        self.setWindowTitle("Choose Random Game - Gaming Dashboard & Live Stream Assistant")
        w = getattr(self.config, 'uiWindowWidth', 1280)
        h = getattr(self.config, 'uiWindowHeight', 780)
        min_w = getattr(self.config, 'uiMinWidth', 1100)
        min_h = getattr(self.config, 'uiMinHeight', 680)
        self.resize(w, h)
        self.setMinimumSize(min_w, min_h)
        self.setStyleSheet(STYLESHEET)

        # Main Central Container
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        self.mainLayout = QVBoxLayout(centralWidget)
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        self.mainLayout.setSpacing(14)

        # 1. Top Bar: Title, Clean Button, and Stat Cards
        self.buildHeaderSection()

        # 2. Navigation Bar (Tabs: Sorteador Geral, Jogo do Dia, GOTY, Escolha do Chat, Histórico de Lives)
        self.buildNavBar()

        # 2.5 Live Gameplay Session Stopwatch Bar
        self.buildSessionBar()

        # 3. Stacked Container for Views
        self.stack = QStackedWidget()
        self.mainLayout.addWidget(self.stack, 1)

        # View 0: Sorteador Geral & Explorador do Banco
        self.viewMain = self.buildMainView()
        self.stack.addWidget(self.viewMain)

        # View 1: Jogo do Dia (Game of the Day)
        self.viewGotd = self.buildGotdView()
        self.stack.addWidget(self.viewGotd)

        # View 2: Jogo do Ano (GOTY)
        self.viewGoty = self.buildGotyView()
        self.stack.addWidget(self.viewGoty)

        # View 3: Escolha do Chat (Sorteio Triplo para Enquete do YouTube)
        self.viewChatChoice = self.buildChatChoiceView()
        self.stack.addWidget(self.viewChatChoice)

        # View 4: Histórico de Lives Anteriores
        self.viewLiveHistory = self.buildLiveHistoryView()
        self.stack.addWidget(self.viewLiveHistory)

        # Debounce timer for search
        self._searchTimer = QTimer(self)
        self._searchTimer.setSingleShot(True)
        self._searchTimer.setInterval(250)
        self._searchTimer.timeout.connect(self.refreshTable)

        # Load Initial Data
        self.updateHeroDisplay(self.currentChoice)
        self.refreshStats()
        self.refreshTable()
        self.onRerollGotd(initial=True)
        self.onRerollGoty()

        # Center Window
        self.centerOnScreen()

    def centerOnScreen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    # -------------------------------------------------------------
    # 1. Header & Stats Section
    # -------------------------------------------------------------
    def buildHeaderSection(self):
        headerLayout = QHBoxLayout()
        headerLayout.setSpacing(10)

        # App Title & Subtitle
        titleBox = QVBoxLayout()
        titleBox.setSpacing(1)
        titleLabel = QLabel("🎮 CHOOSE RANDOM GAME")
        titleLabel.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titleLabel.setStyleSheet("color: #ffffff; letter-spacing: 0.5px;")
        
        subtitleLabel = QLabel("Gaming Backlog & Intelligent Random Launcher")
        subtitleLabel.setFont(QFont("Segoe UI", 8))
        subtitleLabel.setStyleSheet("color: #8c96a8;")
        
        titleBox.addWidget(titleLabel)
        titleBox.addWidget(subtitleLabel)
        headerLayout.addLayout(titleBox)

        # Synchronize Sources Button
        self.btnSyncSources = QPushButton("🔄 Sincronizar Fontes")
        self.btnSyncSources.setObjectName("BtnSecondary")
        self.btnSyncSources.setToolTip("Re-importa e sincroniza todos os jogos (instalados ou não) de todas as fontes (Playnite, eXoDOS, atalhos, pastas)")
        self.btnSyncSources.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnSyncSources.clicked.connect(self.onSyncSources)
        headerLayout.addWidget(self.btnSyncSources)

        # Clean Database Button
        self.btnCleanDb = QPushButton("🧹 Limpar Banco")
        self.btnCleanDb.setObjectName("BtnSecondary")
        self.btnCleanDb.setToolTip("Verifica jogos que não estão mais instalados e os marca como NÃO INSTALADOS (preserva histórico e favoritos)")
        self.btnCleanDb.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnCleanDb.clicked.connect(self.onCleanDatabase)
        headerLayout.addWidget(self.btnCleanDb)

        # 1-Click Playnite Exporter
        self.btnExportPlaynite = QPushButton("⚡ Exportar Playnite")
        self.btnExportPlaynite.setObjectName("BtnSecondary")
        self.btnExportPlaynite.setToolTip("Dispara o script do Playnite para re-exportar a biblioteca completa (jogos de PC e emuladores)")
        self.btnExportPlaynite.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnExportPlaynite.clicked.connect(self.onExportPlaynite)
        headerLayout.addWidget(self.btnExportPlaynite)

        # Web Overlay for OBS
        self.btnWebOverlay = QPushButton("📡 Overlay OBS")
        self.btnWebOverlay.setObjectName("BtnSecondary")
        self.btnWebOverlay.setToolTip("Abre o Overlay HTML5 para OBS Studio no navegador (http://localhost:8089/overlay)")
        self.btnWebOverlay.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnWebOverlay.clicked.connect(self.onOpenWebOverlay)
        headerLayout.addWidget(self.btnWebOverlay)

        # YouTube Channels (Configurados no .ini)
        mainChannelUrl = getattr(self.config, 'streamerYouTubeMainChannel', '').strip()
        liveChannelUrl = getattr(self.config, 'streamerYouTubeLiveChannel', '').strip()

        if mainChannelUrl or liveChannelUrl:
            ytBox = QHBoxLayout()
            ytBox.setSpacing(6)

            if mainChannelUrl:
                mainHandle = extractChannelHandle(mainChannelUrl, "@CanalPrincipal")
                self.btnYtMain = QPushButton(f"📺 Principal: {mainHandle}")
                self.btnYtMain.setCursor(Qt.CursorShape.PointingHandCursor)
                self.btnYtMain.setToolTip(f"Canal Principal no YouTube:\n{mainChannelUrl}")
                self.btnYtMain.setStyleSheet("""
                    QPushButton {
                        background-color: #1a1d26;
                        color: #ff7675;
                        border: 1px solid #ff4757;
                        border-radius: 6px;
                        padding: 4px 10px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #ff4757;
                        color: #ffffff;
                    }
                """)
                self.btnYtMain.clicked.connect(lambda: webbrowser.open(mainChannelUrl))
                ytBox.addWidget(self.btnYtMain)

            if liveChannelUrl:
                liveHandle = extractChannelHandle(liveChannelUrl, "@CanalLives")
                self.btnYtLive = QPushButton(f"🔴 Lives: {liveHandle}")
                self.btnYtLive.setCursor(Qt.CursorShape.PointingHandCursor)
                self.btnYtLive.setToolTip(f"Canal de Lives no YouTube:\n{liveChannelUrl}")
                self.btnYtLive.setStyleSheet("""
                    QPushButton {
                        background-color: #1a1d26;
                        color: #a29bfe;
                        border: 1px solid #6c5ce7;
                        border-radius: 6px;
                        padding: 4px 10px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #6c5ce7;
                        color: #ffffff;
                    }
                """)
                self.btnYtLive.clicked.connect(lambda: webbrowser.open(liveChannelUrl))
                ytBox.addWidget(self.btnYtLive)

            headerLayout.addLayout(ytBox)

        headerLayout.addStretch()

        # 5 Stat Cards
        self.statTotal = self.createStatCard("0", "CATÁLOGO")
        self.statInstalled = self.createStatCard("0", "INSTALADOS")
        self.statPlayed = self.createStatCard("0", "SESSÕES")
        self.statFinished = self.createStatCard("0", "ZERADOS")
        self.statBacklog = self.createStatCard("0%", "CONCLUÍDO")

        headerLayout.addWidget(self.statTotal)
        headerLayout.addWidget(self.statInstalled)
        headerLayout.addWidget(self.statPlayed)
        headerLayout.addWidget(self.statFinished)
        headerLayout.addWidget(self.statBacklog)

        self.mainLayout.addLayout(headerLayout)

    def createStatCard(self, initialValue, labelText):
        card = QFrame()
        card.setObjectName("StatCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(2)

        valLabel = QLabel(initialValue)
        valLabel.setObjectName("StatValue")
        valLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        descLabel = QLabel(labelText)
        descLabel.setObjectName("StatLabel")
        descLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(valLabel)
        layout.addWidget(descLabel)
        return card

    # -------------------------------------------------------------
    # 2. Navigation Bar
    # -------------------------------------------------------------
    def buildNavBar(self):
        navLayout = QHBoxLayout()
        navLayout.setSpacing(10)

        self.btnNavMain = QPushButton("🎲 Sorteador & Explorador")
        self.btnNavMain.setProperty("class", "NavBtn")
        self.btnNavMain.setCheckable(True)
        self.btnNavMain.setChecked(True)
        self.btnNavMain.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnNavMain.clicked.connect(lambda: self.switchView(0))

        self.btnNavGotd = QPushButton("🌟 Jogo do Dia")
        self.btnNavGotd.setProperty("class", "NavBtn")
        self.btnNavGotd.setCheckable(True)
        self.btnNavGotd.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnNavGotd.clicked.connect(lambda: self.switchView(1))

        self.btnNavGoty = QPushButton("🏆 Jogos do Ano (GOTY)")
        self.btnNavGoty.setProperty("class", "NavBtn")
        self.btnNavGoty.setCheckable(True)
        self.btnNavGoty.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnNavGoty.clicked.connect(lambda: self.switchView(2))

        self.btnNavChatChoice = QPushButton("🗳️ Escolha do Chat")
        self.btnNavChatChoice.setProperty("class", "NavBtn")
        self.btnNavChatChoice.setCheckable(True)
        self.btnNavChatChoice.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnNavChatChoice.clicked.connect(lambda: self.switchView(3))

        self.btnNavLiveHistory = QPushButton("📜 Histórico de Lives")
        self.btnNavLiveHistory.setProperty("class", "NavBtn")
        self.btnNavLiveHistory.setCheckable(True)
        self.btnNavLiveHistory.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnNavLiveHistory.clicked.connect(lambda: self.switchView(4))

        self.navGroup = QButtonGroup(self)
        self.navGroup.addButton(self.btnNavMain)
        self.navGroup.addButton(self.btnNavGotd)
        self.navGroup.addButton(self.btnNavGoty)
        self.navGroup.addButton(self.btnNavChatChoice)
        self.navGroup.addButton(self.btnNavLiveHistory)

        navLayout.addWidget(self.btnNavMain)
        navLayout.addWidget(self.btnNavGotd)
        navLayout.addWidget(self.btnNavGoty)
        navLayout.addWidget(self.btnNavChatChoice)
        navLayout.addWidget(self.btnNavLiveHistory)
        navLayout.addStretch()

        # Streamer & OBS Controls
        self.chkRoulette = QCheckBox("🎰 Roleta Live")
        self.chkRoulette.setChecked(getattr(self.config, 'streamerRouletteEnabled', True))
        self.chkRoulette.setToolTip("Ativa o efeito visual de slot machine/roleta com suspense antes de revelar o jogo")
        self.chkRoulette.setStyleSheet("color: #00cec9; font-weight: bold; font-size: 11px;")
        navLayout.addWidget(self.chkRoulette)

        self.btnObsOverlay = QPushButton("🎥 Overlay OBS")
        self.btnObsOverlay.setObjectName("BtnSecondary")
        self.btnObsOverlay.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnObsOverlay.setToolTip("Abre uma janela limpa com capa e título para captura direta de janela no OBS Studio")
        self.btnObsOverlay.clicked.connect(self.onOpenObsOverlay)
        navLayout.addWidget(self.btnObsOverlay)

        self.mainLayout.addLayout(navLayout)

    def buildSessionBar(self):
        self.sessionBar = QFrame()
        self.sessionBar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e1b4b, stop:0.5 #0f172a, stop:1 #064e3b);
                border: 2px solid #10b981;
                border-radius: 10px;
                padding: 6px 14px;
            }
        """)
        sLayout = QHBoxLayout(self.sessionBar)
        sLayout.setContentsMargins(8, 4, 8, 4)
        sLayout.setSpacing(12)

        self.lblSessionStatus = QLabel("🔴 SESSÃO DE GAMEPLAY ATIVA:")
        self.lblSessionStatus.setStyleSheet("color: #34d399; font-weight: 900; font-size: 12px; letter-spacing: 0.5px;")
        sLayout.addWidget(self.lblSessionStatus)

        self.lblSessionGame = QLabel("Nenhum jogo em execução")
        self.lblSessionGame.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 13px;")
        sLayout.addWidget(self.lblSessionGame)

        sLayout.addStretch()

        self.lblSessionTime = QLabel("⏱️ 00:00:00")
        self.lblSessionTime.setStyleSheet("color: #38bdf8; font-weight: 900; font-size: 14px; font-family: monospace;")
        sLayout.addWidget(self.lblSessionTime)

        self.btnStopSession = QPushButton("⏹️ Encerrar Sessão & Salvar")
        self.btnStopSession.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnStopSession.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
                border-radius: 6px;
                padding: 5px 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        self.btnStopSession.clicked.connect(self.onStopGameplaySession)
        sLayout.addWidget(self.btnStopSession)

        self.mainLayout.addWidget(self.sessionBar)
        self.sessionBar.hide()

    def switchView(self, index):
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.btnNavMain.setChecked(True)
        elif index == 1:
            self.btnNavGotd.setChecked(True)
        elif index == 2:
            self.btnNavGoty.setChecked(True)
            self.refreshGotyTable()
        elif index == 3:
            self.btnNavChatChoice.setChecked(True)
            if not self.chatChoiceTrio:
                self.onRerollChatChoice()
        elif index == 4:
            self.btnNavLiveHistory.setChecked(True)
            self.refreshLiveHistoryTable()

    # -------------------------------------------------------------
    # 3. View 0: Sorteador Geral & Explorador do Banco
    # -------------------------------------------------------------
    def buildMainView(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Quick Live Themes Bar
        themeRow = QHBoxLayout()
        themeRow.setSpacing(8)
        themeLbl = QLabel("🎯 TEMA DA LIVE:")
        themeLbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        themeLbl.setStyleSheet("color: #00cec9; letter-spacing: 1px;")
        themeRow.addWidget(themeLbl)

        themes = [
            ("🌟 Todos", "all"),
            ("🆕 Backlog Zero (0x)", "backlog"),
            ("🎮 Emuladores", "emulators"),
            ("🕹️ Só Retrô (eXoDOS)", "retro"),
            ("🚀 Só PC / Lojas", "modern"),
            ("⭐ Favoritos", "favorites")
        ]
        for t_label, t_mode in themes:
            btn = QPushButton(t_label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #161a24;
                    border: 1px solid #2b3244;
                    border-radius: 6px;
                    padding: 5px 12px;
                    font-size: 11px;
                    font-weight: bold;
                    color: #cbd5e1;
                }
                QPushButton:hover {
                    background-color: #222938;
                    border-color: #00cec9;
                    color: #ffffff;
                }
            """)
            btn.clicked.connect(lambda _, m=t_mode: self.onApplyLiveTheme(m))
            themeRow.addWidget(btn)

        themeRow.addStretch()
        layout.addLayout(themeRow)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)

        heroContainer = self.buildHeroCard()
        splitter.addWidget(heroContainer)

        browserContainer = self.buildDatabaseBrowser()
        splitter.addWidget(browserContainer)

        splitter.setSizes([460, 680])
        layout.addWidget(splitter)
        return widget

    def buildHeroCard(self):
        card = QFrame()
        card.setObjectName("HeroCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Section Header
        heroHeader = QHBoxLayout()
        headerText = QLabel("🎯 JOGO SORTEADO")
        headerText.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        headerText.setStyleSheet("color: #00cec9; letter-spacing: 1px;")
        
        self.installBadge = QLabel("✔ INSTALADO")
        self.installBadge.setObjectName("InstallBadge")
        self.installBadge.setStyleSheet(
            "background-color: #00b894; color: #ffffff; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;"
        )

        self.platformBadge = QLabel("LOCAL")
        self.platformBadge.setObjectName("PlatformBadge")

        self.hltbBadge = QLabel("⏱️ HLTB: --")
        self.hltbBadge.setObjectName("HltbBadge")
        self.hltbBadge.setStyleSheet(
            "background-color: #8b5cf6; color: #ffffff; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;"
        )
        
        heroHeader.addWidget(headerText)
        heroHeader.addStretch()
        heroHeader.addWidget(self.installBadge)
        heroHeader.addWidget(self.platformBadge)
        heroHeader.addWidget(self.hltbBadge)
        layout.addLayout(heroHeader)

        # Cover Image Box
        imgFrame = QFrame()
        imgFrame.setStyleSheet("background-color: #0d0f14; border: 1px solid #242b3b; border-radius: 10px;")
        imgLayout = QVBoxLayout(imgFrame)
        imgLayout.setContentsMargins(6, 6, 6, 6)

        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cover_w = getattr(self.config, 'uiCoverWidth', 160)
        cover_h = getattr(self.config, 'uiCoverHeight', 160)
        self.imageLabel.setFixedSize(cover_w, cover_h)
        imgLayout.addWidget(self.imageLabel, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(imgFrame, 0, Qt.AlignmentFlag.AlignCenter)

        # Game Title
        self.gameTitleLabel = QLabel("Nome do Jogo")
        self.gameTitleLabel.setObjectName("GameTitle")
        self.gameTitleLabel.setWordWrap(True)
        self.gameTitleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.gameTitleLabel)

        # Game Stats Row
        self.gameStatsLabel = QLabel("Vezes jogado: 0 • Status: Em aberto")
        self.gameStatsLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gameStatsLabel.setStyleSheet("color: #8c96a8; font-size: 12px;")
        layout.addWidget(self.gameStatsLabel)

        layout.addSpacing(4)

        # Big Play Button
        self.btnPlay = QPushButton("▶  JOGAR AGORA")
        self.btnPlay.setObjectName("BtnPlay")
        self.btnPlay.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnPlay.clicked.connect(self.onPlayHero)
        layout.addWidget(self.btnPlay)

        # Reroll Button
        self.btnReroll = QPushButton("🎲  SORTEAR NOVO JOGO (REROLL)")
        self.btnReroll.setObjectName("BtnReroll")
        self.btnReroll.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnReroll.clicked.connect(self.onRerollHero)
        layout.addWidget(self.btnReroll)

        # Intel & Streamer Actions (Row 1)
        intelRow = QHBoxLayout()
        intelRow.setSpacing(8)

        self.btnHeroIntel = QPushButton("ℹ️ Guia & Dicas")
        self.btnHeroIntel.setObjectName("BtnSecondary")
        self.btnHeroIntel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnHeroIntel.setToolTip("Abre central com sinopse, estimativas do HowLongToBeat e detonados")
        self.btnHeroIntel.clicked.connect(self.onOpenHeroIntel)

        self.btnRecordHeroLive = QPushButton("🔴 Gravar na Live")
        self.btnRecordHeroLive.setObjectName("BtnSecondary")
        self.btnRecordHeroLive.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnRecordHeroLive.setToolTip("Registra este jogo no histórico de transmissões ao vivo do seu canal")
        self.btnRecordHeroLive.clicked.connect(self.onRecordCurrentHeroLive)

        intelRow.addWidget(self.btnHeroIntel)
        intelRow.addWidget(self.btnRecordHeroLive)
        layout.addLayout(intelRow)

        # Streamer Suite Actions (Row 2: Roda da Fortuna, Modo Misterioso, Card da Live)
        suiteRow = QHBoxLayout()
        suiteRow.setSpacing(6)

        self.btnWheelOfFortune = QPushButton("🎡 Roda da Fortuna")
        self.btnWheelOfFortune.setObjectName("BtnSecondary")
        self.btnWheelOfFortune.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnWheelOfFortune.setToolTip("Gira a Roda da Fortuna com física e suspense para escolher o jogo")
        self.btnWheelOfFortune.clicked.connect(self.onOpenWheelOfFortune)
        suiteRow.addWidget(self.btnWheelOfFortune)

        self.btnMysteryMode = QPushButton("🕵️ Misterioso")
        self.btnMysteryMode.setObjectName("BtnSecondary")
        self.btnMysteryMode.setCheckable(True)
        self.btnMysteryMode.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnMysteryMode.setToolTip("Modo Jogo Misterioso: oculta a capa e título até você ou o chat revelarem")
        self.btnMysteryMode.clicked.connect(self.onToggleMysteryMode)
        suiteRow.addWidget(self.btnMysteryMode)

        self.btnSocialCard = QPushButton("📸 Card da Live")
        self.btnSocialCard.setObjectName("BtnSecondary")
        self.btnSocialCard.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnSocialCard.setToolTip("Gera imagem 1200x630 promocional para Comunidade do YouTube, Discord e Twitter")
        self.btnSocialCard.clicked.connect(self.onGenerateSocialCard)
        suiteRow.addWidget(self.btnSocialCard)

        layout.addLayout(suiteRow)

        # Filter Category for Reroll
        filterRow = QHBoxLayout()
        filterLbl = QLabel("Filtrar sorteio:")
        filterLbl.setStyleSheet("color: #8c96a8; font-size: 11px;")
        
        self.comboRerollFilter = QComboBox()
        self.comboRerollFilter.addItems([
            "Todas as Fontes",
            "Apenas Instalados (Prontos p/ Jogar)",
            "Apenas Não Instalados (p/ Baixar)",
            "Apenas Favoritos (⭐)",
            "Apenas Emuladores / Consoles (Playnite)",
            "Apenas Playnite (Lojas & Emuladores)",
            "Apenas eXoDOS (Instalados)",
            "Apenas Atalhos / Desktop",
            "Apenas Pastas Locais",
            "⏱️ Jogos Curtos (< 5h HLTB)",
            "⏱️ Jogos Médios (5-15h HLTB)",
            "⏱️ Jogos Longos (> 25h HLTB)"
        ])
        self.comboRerollFilter.currentIndexChanged.connect(self.onRerollHero)
        filterRow.addWidget(filterLbl)
        filterRow.addWidget(self.comboRerollFilter, 1)
        layout.addLayout(filterRow)

        layout.addStretch()

        # Action Buttons (Favorite / Finish)
        actionsRow = QHBoxLayout()
        self.btnFavorite = QPushButton("⭐ Favoritar")
        self.btnFavorite.setObjectName("BtnSecondary")
        self.btnFavorite.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnFavorite.clicked.connect(self.onToggleFavorite)

        self.btnFinish = QPushButton("✔ Marcar Zerado")
        self.btnFinish.setObjectName("BtnSecondary")
        self.btnFinish.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnFinish.clicked.connect(self.onToggleFinished)

        actionsRow.addWidget(self.btnFavorite)
        actionsRow.addWidget(self.btnFinish)
        layout.addLayout(actionsRow)

        return card


    def buildDatabaseBrowser(self):
        container = QFrame()
        container.setStyleSheet("background-color: #12151d; border: 1px solid #242b3b; border-radius: 14px; padding: 14px;")
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        # Header with Search and Filter
        topRow = QHBoxLayout()
        
        browserTitle = QLabel("📚 EXPLORADOR DO BANCO")
        browserTitle.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        browserTitle.setStyleSheet("color: #ffffff; letter-spacing: 1px;")
        topRow.addWidget(browserTitle)
        topRow.addStretch()

        # Search Bar
        self.searchBox = QLineEdit()
        self.searchBox.setPlaceholderText("🔍 Buscar jogo pelo título...")
        self.searchBox.setFixedWidth(230)
        self.searchBox.textChanged.connect(self.onSearchChanged)
        topRow.addWidget(self.searchBox)

        # Filter Dropdown
        self.filterCombo = QComboBox()
        self.filterCombo.addItems(["Todos", "Instalados", "Não Instalados", "Não Jogados", "Zerados", "Favoritos"])
        self.filterCombo.currentIndexChanged.connect(self.onFilterChanged)
        topRow.addWidget(self.filterCombo)

        layout.addLayout(topRow)

        # Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Jogo / Título", "Origem", "Instalação", "Vezes", "Último Acesso", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.onTableDoubleClicked)
        self.table.itemSelectionChanged.connect(self.onTableSelectionChanged)
        layout.addWidget(self.table, 1)

        # Bottom Actions for Selected Table Game
        botRow = QHBoxLayout()
        hintLabel = QLabel("💡 Dica: Dê duplo clique em qualquer linha para jogar ou instalar")
        hintLabel.setStyleSheet("color: #718096; font-size: 11px;")
        botRow.addWidget(hintLabel)
        botRow.addStretch()

        self.btnPlaySelected = QPushButton("▶ Jogar Selecionado")
        self.btnPlaySelected.setObjectName("BtnSecondary")
        self.btnPlaySelected.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnPlaySelected.clicked.connect(self.onPlaySelected)
        botRow.addWidget(self.btnPlaySelected)

        layout.addLayout(botRow)
        return container

    # -------------------------------------------------------------
    # 4. View 1: Jogo do Dia (Game of the Day)
    # -------------------------------------------------------------
    def buildGotdView(self):
        container = QWidget()
        layout = QVBoxLayout(container)
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
        tagLabel = QLabel("🌟 RECOMENDAÇÃO DO DIA • 100% INSTALADO NO SEU PC")
        tagLabel.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        tagLabel.setStyleSheet("color: #00cec9; letter-spacing: 1px;")
        tagRow.addWidget(tagLabel)
        tagRow.addStretch()

        self.gotdPlatformBadge = QLabel("LOCAL")
        self.gotdPlatformBadge.setObjectName("PlatformBadge")
        tagRow.addWidget(self.gotdPlatformBadge)
        cardLayout.addLayout(tagRow)

        # Image cover
        imgFrame = QFrame()
        imgFrame.setStyleSheet("background-color: #0d0f14; border: 1px solid #242b3b; border-radius: 12px;")
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
        self.btnGotdPlay = QPushButton("▶  JOGAR JOGO DO DIA AGORA")
        self.btnGotdPlay.setObjectName("BtnPlay")
        self.btnGotdPlay.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnGotdPlay.clicked.connect(self.onPlayGotd)
        cardLayout.addWidget(self.btnGotdPlay)

        # Reroll Button
        self.btnGotdReroll = QPushButton("🎲  SORTEAR OUTRA RECOMENDAÇÃO DO DIA")
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
        return container

    # -------------------------------------------------------------
    # 5. View 2: Jogos do Ano (GOTY Hall of Fame)
    # -------------------------------------------------------------
    def buildGotyView(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Upper Card: Random GOTY Spotlight
        card = QFrame()
        card.setObjectName("GotyCard")
        cardLayout = QVBoxLayout(card)
        cardLayout.setContentsMargins(22, 18, 22, 18)
        cardLayout.setSpacing(10)

        # Year & Tag Row
        topRow = QHBoxLayout()
        self.gotyYearBadge = QLabel("🏆 GAME OF THE YEAR - ANO 2024")
        self.gotyYearBadge.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.gotyYearBadge.setStyleSheet("color: #d4af37; letter-spacing: 1px;")
        topRow.addWidget(self.gotyYearBadge)
        topRow.addStretch()

        self.gotyInstalledBadge = QLabel("NÃO INSTALADO")
        self.gotyInstalledBadge.setObjectName("PlatformBadge")
        topRow.addWidget(self.gotyInstalledBadge)
        cardLayout.addLayout(topRow)

        # Content Row (Cover Image + Details)
        contentRow = QHBoxLayout()
        contentRow.setSpacing(20)

        # Cover Frame
        imgFrame = QFrame()
        imgFrame.setStyleSheet("background-color: #0d0f14; border: 1px solid #242b3b; border-radius: 12px;")
        imgLayout = QVBoxLayout(imgFrame)
        imgLayout.setContentsMargins(6, 6, 6, 6)

        self.gotyImageLabel = QLabel()
        self.gotyImageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gotyImageLabel.setFixedSize(160, 160)
        imgLayout.addWidget(self.gotyImageLabel, 0, Qt.AlignmentFlag.AlignCenter)
        contentRow.addWidget(imgFrame, 0, Qt.AlignmentFlag.AlignTop)

        # Details Column
        detailsCol = QVBoxLayout()
        detailsCol.setSpacing(6)

        # Title & Developer
        self.gotyTitleLabel = QLabel("Astro Bot")
        self.gotyTitleLabel.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.gotyTitleLabel.setStyleSheet("color: #ffffff;")
        detailsCol.addWidget(self.gotyTitleLabel)

        self.gotyMetaLabel = QLabel("Team Asobi • Plataforma 3D • The Game Awards (GOTY), Golden Joystick")
        self.gotyMetaLabel.setStyleSheet("color: #e5c158; font-size: 13px; font-weight: bold;")
        detailsCol.addWidget(self.gotyMetaLabel)

        self.gotySummaryLabel = QLabel("Uma celebração vibrante e criativa da história dos videogames...")
        self.gotySummaryLabel.setWordWrap(True)
        self.gotySummaryLabel.setStyleSheet("color: #cbd5e1; font-size: 13px; line-height: 1.4;")
        detailsCol.addWidget(self.gotySummaryLabel)

        gotyHint = QLabel("💡 O sorteio de GOTY abrange todos os vencedores oficiais da história (instalados ou não). Se você o tiver instalado, poderá jogá-lo imediatamente!")
        gotyHint.setStyleSheet("color: #8c96a8; font-size: 11px; font-style: italic;")
        detailsCol.addWidget(gotyHint)

        contentRow.addLayout(detailsCol, 1)
        cardLayout.addLayout(contentRow)

        # Buttons
        btnRow = QHBoxLayout()
        btnRow.setSpacing(10)

        self.btnGotyPlay = QPushButton("▶  JOGAR GOTY INSTALADO")
        self.btnGotyPlay.setObjectName("BtnGoty")
        self.btnGotyPlay.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnGotyPlay.clicked.connect(self.onPlayGoty)
        btnRow.addWidget(self.btnGotyPlay)

        self.btnGotyIntel = QPushButton("ℹ️ Detonados & Guia")
        self.btnGotyIntel.setObjectName("BtnSecondary")
        self.btnGotyIntel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnGotyIntel.clicked.connect(self.onOpenGotyIntel)
        btnRow.addWidget(self.btnGotyIntel)

        self.btnGotyExplore = QPushButton("🌐 Loja / Google")
        self.btnGotyExplore.setObjectName("BtnSecondary")
        self.btnGotyExplore.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnGotyExplore.clicked.connect(self.onExploreGoty)
        btnRow.addWidget(self.btnGotyExplore)

        self.btnGotyReroll = QPushButton("🎲 Sortear Outro GOTY")
        self.btnGotyReroll.setObjectName("BtnReroll")
        self.btnGotyReroll.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnGotyReroll.clicked.connect(self.onRerollGoty)
        btnRow.addWidget(self.btnGotyReroll)


        btnRow.addStretch()
        cardLayout.addLayout(btnRow)
        layout.addWidget(card)

        # Lower Table: Full GOTY History
        tableContainer = QFrame()
        tableContainer.setStyleSheet("background-color: #12151d; border: 1px solid #242b3b; border-radius: 12px; padding: 12px;")
        tLayout = QVBoxLayout(tableContainer)
        tLayout.setSpacing(8)

        tHeader = QHBoxLayout()
        tTitle = QLabel("🏛️ HALL DA FAMA DOS VENCEDORES DO GOTY (1983 - 2025)")
        tTitle.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        tTitle.setStyleSheet("color: #d4af37; letter-spacing: 1px;")
        tHeader.addWidget(tTitle)
        tHeader.addStretch()

        self.gotySearchBox = QLineEdit()
        self.gotySearchBox.setPlaceholderText("🔍 Filtrar vencedores por nome ou ano...")
        self.gotySearchBox.setFixedWidth(280)
        self.gotySearchBox.textChanged.connect(self.onGotySearchChanged)
        tHeader.addWidget(self.gotySearchBox)
        tLayout.addLayout(tHeader)

        self.gotyTable = QTableWidget()
        self.gotyTable.setColumnCount(6)
        self.gotyTable.setHorizontalHeaderLabels(["Ano", "Título do GOTY", "Desenvolvedora / Estúdio", "Gênero", "Premiações Principais", "No Seu PC?"])
        self.gotyTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.gotyTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.gotyTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.gotyTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.gotyTable.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.gotyTable.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.gotyTable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.gotyTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.gotyTable.doubleClicked.connect(self.onGotyTableDoubleClicked)
        tLayout.addWidget(self.gotyTable, 1)

        layout.addWidget(tableContainer, 1)
        return container

    # -------------------------------------------------------------
    # 6. View 3: Escolha do Chat (Sorteio Triplo para Enquete do YouTube)
    # -------------------------------------------------------------
    def buildChatChoiceView(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(14)

        # Header Bar
        header = QHBoxLayout()
        hTitle = QLabel("🗳️ ESCOLHA DO CHAT • ENQUETE AO VIVO DO YOUTUBE")
        hTitle.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        hTitle.setStyleSheet("color: #00cec9; letter-spacing: 1px;")
        header.addWidget(hTitle)
        header.addStretch()

        self.btnCopyPoll = QPushButton("📋 Copiar Enquete para o Chat")
        self.btnCopyPoll.setObjectName("BtnSecondary")
        self.btnCopyPoll.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnCopyPoll.setToolTip("Copia o texto formatado das 3 opções para abrir a enquete no chat da live")
        self.btnCopyPoll.clicked.connect(self.onCopyChatPoll)
        header.addWidget(self.btnCopyPoll)

        self.btnRerollTrio = QPushButton("🎲 Sortear 3 Novas Opções")
        self.btnRerollTrio.setObjectName("BtnReroll")
        self.btnRerollTrio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnRerollTrio.clicked.connect(self.onRerollChatChoice)
        header.addWidget(self.btnRerollTrio)
        layout.addLayout(header)

        hint = QLabel("💡 Sorteie 3 jogos distintos instalados no seu PC. Abra a enquete na sua live do YouTube e clique em 'JOGAR' na opção mais votada pelo seu público!")
        hint.setStyleSheet("color: #8c96a8; font-size: 11px; font-style: italic;")
        layout.addWidget(hint)

        # 3 Cards Container
        self.trioContainer = QHBoxLayout()
        self.trioContainer.setSpacing(16)
        self.trioCards = []

        labels = [
            ("OPÇÃO A", "#00cec9", "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00b894, stop:1 #00cec9)", "#0d0f14"),
            ("OPÇÃO B", "#fdcb6e", "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e67e22, stop:1 #fdcb6e)", "#0d0f14"),
            ("OPÇÃO C", "#e17055", "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d63031, stop:1 #e17055)", "#ffffff")
        ]
        for i, (opt_name, color, btn_gradient, btn_text_color) in enumerate(labels):
            card = QFrame()
            card.setObjectName(f"TrioCard_{i}")
            card.setStyleSheet(f"""
                QFrame#TrioCard_{i} {{
                    background-color: #12151d;
                    border: 2px solid {color};
                    border-radius: 14px;
                    padding: 14px;
                }}
            """)
            cLayout = QVBoxLayout(card)
            cLayout.setSpacing(10)

            # Option Badge
            optBadge = QLabel(opt_name)
            optBadge.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            optBadge.setStyleSheet(f"background-color: {color}; color: #0d0f14; border-radius: 6px; padding: 4px 12px; font-weight: bold; border: none;")
            optBadge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cLayout.addWidget(optBadge)

            # Cover Box
            imgFrame = QFrame()
            imgFrame.setObjectName(f"TrioImgFrame_{i}")
            imgFrame.setStyleSheet(f"""
                QFrame#TrioImgFrame_{i} {{
                    background-color: #0d0f14;
                    border: 1px solid #242b3b;
                    border-radius: 10px;
                }}
            """)
            imgLayout = QVBoxLayout(imgFrame)
            imgLayout.setContentsMargins(6, 6, 6, 6)

            coverLabel = QLabel()
            coverLabel.setFixedSize(160, 160)
            coverLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            coverLabel.setStyleSheet("border: none; background: transparent;")
            imgLayout.addWidget(coverLabel, 0, Qt.AlignmentFlag.AlignCenter)
            cLayout.addWidget(imgFrame, 0, Qt.AlignmentFlag.AlignCenter)

            # Title
            titleLabel = QLabel("Aguardando sorteio...")
            titleLabel.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            titleLabel.setStyleSheet("color: #ffffff; background: transparent; border: none;")
            titleLabel.setWordWrap(True)
            titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cLayout.addWidget(titleLabel)

            # Platform & Stats
            metaLabel = QLabel("Pronto para rodar")
            metaLabel.setFont(QFont("Segoe UI", 11))
            metaLabel.setStyleSheet("color: #a0aec0; background: transparent; border: none;")
            metaLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cLayout.addWidget(metaLabel)

            cLayout.addStretch()

            # Play Button (Winner)
            btnPlayOpt = QPushButton(f"▶ JOGAR {opt_name} (Vencedor)")
            btnPlayOpt.setCursor(Qt.CursorShape.PointingHandCursor)
            btnPlayOpt.setStyleSheet(f"""
                QPushButton {{
                    background: {btn_gradient};
                    color: {btn_text_color};
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 13px;
                    font-weight: bold;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 16px;
                }}
                QPushButton:hover {{
                    background: {color};
                    color: {btn_text_color};
                }}
                QPushButton:pressed {{
                    background-color: #2d3436;
                    color: #ffffff;
                }}
            """)
            btnPlayOpt.clicked.connect(lambda _, idx=i: self.onPlayChatChoice(idx))
            cLayout.addWidget(btnPlayOpt)

            # Voting & Polling Row
            voteRow = QHBoxLayout()
            voteRow.setSpacing(6)

            lblVoteCount = QLabel("0 votos (0%)")
            lblVoteCount.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lblVoteCount.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")

            btnVote = QPushButton("🗳️ +1 Voto")
            btnVote.setCursor(Qt.CursorShape.PointingHandCursor)
            btnVote.setStyleSheet("""
                QPushButton {
                    background-color: #1e293b;
                    border: 1px solid #0284c7;
                    color: #38bdf8;
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 6px;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background-color: #0369a1;
                    color: #ffffff;
                }
            """)
            btnVote.clicked.connect(lambda _, idx=i: self.onAddChatVote(idx))
            voteRow.addWidget(lblVoteCount, 1)
            voteRow.addWidget(btnVote)
            cLayout.addLayout(voteRow)

            # Intel Button
            btnIntelOpt = QPushButton("ℹ️ Guia & Dicas")
            btnIntelOpt.setCursor(Qt.CursorShape.PointingHandCursor)
            btnIntelOpt.setStyleSheet("""
                QPushButton {
                    background-color: #1a202c;
                    border: 1px solid #334155;
                    color: #e2e8f0;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 12px;
                    font-weight: 600;
                    border-radius: 6px;
                    padding: 8px 14px;
                }
                QPushButton:hover {
                    background-color: #273449;
                    border-color: #64748b;
                    color: #ffffff;
                }
            """)
            btnIntelOpt.clicked.connect(lambda _, idx=i: self.onOpenChatChoiceIntel(idx))
            cLayout.addWidget(btnIntelOpt)

            self.trioContainer.addWidget(card)
            self.trioCards.append({
                "card": card,
                "coverLabel": coverLabel,
                "titleLabel": titleLabel,
                "metaLabel": metaLabel,
                "lblVoteCount": lblVoteCount,
                "gameEntry": ""
            })

        layout.addLayout(self.trioContainer, 1)
        return container

    # -------------------------------------------------------------
    # 7. View 4: Histórico de Lives Anteriores
    # -------------------------------------------------------------
    def buildLiveHistoryView(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header Bar
        topBar = QHBoxLayout()
        hTitle = QLabel("📜 HISTÓRICO DE TRANSMISSÕES AO VIVO NO YOUTUBE")
        hTitle.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        hTitle.setStyleSheet("color: #d4af37; letter-spacing: 1px;")
        topBar.addWidget(hTitle)
        topBar.addStretch()

        self.btnRefreshLiveHistory = QPushButton("🔄 Atualizar")
        self.btnRefreshLiveHistory.setObjectName("BtnSecondary")
        self.btnRefreshLiveHistory.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnRefreshLiveHistory.clicked.connect(self.refreshLiveHistoryTable)
        topBar.addWidget(self.btnRefreshLiveHistory)
        layout.addLayout(topBar)

        # YouTube Channels Showcase Banner (se configurados no .ini)
        mainChannelUrl = getattr(self.config, 'streamerYouTubeMainChannel', '').strip()
        liveChannelUrl = getattr(self.config, 'streamerYouTubeLiveChannel', '').strip()

        if mainChannelUrl or liveChannelUrl:
            mainHandle = extractChannelHandle(mainChannelUrl, "@CanalPrincipal")
            liveHandle = extractChannelHandle(liveChannelUrl, "@CanalLives")

            channelBanner = QFrame()
            channelBanner.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #151821, stop:1 #201a2d);
                    border: 1px solid #6c5ce7;
                    border-radius: 8px;
                    padding: 6px 12px;
                }
            """)
            cbLayout = QHBoxLayout(channelBanner)
            cbLayout.setContentsMargins(6, 4, 6, 4)
            cbLayout.setSpacing(10)

            bannerParts = []
            if liveChannelUrl:
                bannerParts.append(f"<b>🔴 Canal de Lives:</b> <a href='{liveChannelUrl}' style='color: #a29bfe; text-decoration: none;'>{liveHandle}</a>")
            if mainChannelUrl:
                bannerParts.append(f"<b>📺 Canal Principal:</b> <a href='{mainChannelUrl}' style='color: #ff7675; text-decoration: none;'>{mainHandle}</a>")

            bannerText = QLabel(" &nbsp;&nbsp;|&nbsp;&nbsp; ".join(bannerParts))
            bannerText.setFont(QFont("Segoe UI", 10))
            bannerText.setStyleSheet("color: #e2e8f0;")
            bannerText.setOpenExternalLinks(True)
            cbLayout.addWidget(bannerText)
            cbLayout.addStretch()

            if liveChannelUrl:
                btnOpenLiveYt = QPushButton("🔴 Abrir Canal de Lives")
                btnOpenLiveYt.setObjectName("BtnSecondary")
                btnOpenLiveYt.setCursor(Qt.CursorShape.PointingHandCursor)
                btnOpenLiveYt.setStyleSheet("font-size: 11px; padding: 4px 8px;")
                btnOpenLiveYt.clicked.connect(lambda: webbrowser.open(liveChannelUrl))
                cbLayout.addWidget(btnOpenLiveYt)

            if mainChannelUrl:
                btnOpenMainYt = QPushButton("📺 Abrir Canal Principal")
                btnOpenMainYt.setObjectName("BtnSecondary")
                btnOpenMainYt.setCursor(Qt.CursorShape.PointingHandCursor)
                btnOpenMainYt.setStyleSheet("font-size: 11px; padding: 4px 8px;")
                btnOpenMainYt.clicked.connect(lambda: webbrowser.open(mainChannelUrl))
                cbLayout.addWidget(btnOpenMainYt)

            layout.addWidget(channelBanner)

        # Add Live Entry Bar
        entryFrame = QFrame()
        entryFrame.setStyleSheet("background-color: #12151d; border: 1px solid #242b3b; border-radius: 10px; padding: 10px;")
        eLayout = QHBoxLayout(entryFrame)
        eLayout.setSpacing(10)

        eLabel = QLabel("Anotação da live:")
        eLabel.setStyleSheet("color: #a0aec0; font-weight: bold; font-size: 11px;")
        eLayout.addWidget(eLabel)

        self.liveNotesInput = QLineEdit()
        self.liveNotesInput.setPlaceholderText("Ex: Live #14 - Zeramos a primeira metade, boss derrotado!")
        eLayout.addWidget(self.liveNotesInput, 1)

        self.btnRegisterCurrentLive = QPushButton("➕ Registrar Live com Jogo Atual")
        self.btnRegisterCurrentLive.setObjectName("BtnSecondary")
        self.btnRegisterCurrentLive.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnRegisterCurrentLive.clicked.connect(self.onAddCustomLiveRecord)
        eLayout.addWidget(self.btnRegisterCurrentLive)
        layout.addWidget(entryFrame)

        # Live History Table
        self.liveTable = QTableWidget()
        self.liveTable.setColumnCount(5)
        self.liveTable.setHorizontalHeaderLabels(["ID", "Data da Live", "Jogo Transmitido", "Duração Estimada", "Anotações do Streamer"])
        self.liveTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.liveTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.liveTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.liveTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.liveTable.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.liveTable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.liveTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.liveTable, 1)

        # Delete Action
        delRow = QHBoxLayout()
        self.btnDeleteLiveRecord = QPushButton("🗑️ Excluir Registro Selecionado")
        self.btnDeleteLiveRecord.setObjectName("BtnSecondary")
        self.btnDeleteLiveRecord.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnDeleteLiveRecord.clicked.connect(self.onDeleteSelectedLiveRecord)
        delRow.addWidget(self.btnDeleteLiveRecord)
        delRow.addStretch()
        layout.addLayout(delRow)

        return container


    # -------------------------------------------------------------
    # Logics & Updates: Hero Card
    # -------------------------------------------------------------
    def updateHeroDisplay(self, gameEntry):
        self.currentChoice = gameEntry
        display_name = formatDisplayName(gameEntry)
        platform = detectPlatform(gameEntry)

        # Check Mystery Mode
        if self.isMysteryMode and not self.mysteryRevealed:
            self.gameTitleLabel.setText("🕵️ JOGO MISTERIOSO\n(Clique aqui ou na capa para revelar!)")
            self.gameTitleLabel.setCursor(Qt.CursorShape.PointingHandCursor)
            self.platformBadge.setText("MISTERIOSO")
            self.platformBadge.setStyleSheet("background-color: #6366f1; color: #ffffff; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;")
            self.hltbBadge.setText("⏱️ ??h (HLTB)")
            self.hltbBadge.setStyleSheet("background-color: #475569; color: #cbd5e1; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;")
            self.gameStatsLabel.setText("Modo suspense ativado! Capa e título ocultos para o chat.")
            
            # Render Mystery Box Pixmap
            m_pix = QPixmap(160, 160)
            m_pix.fill(QColor("#0f172a"))
            painter = QPainter(m_pix)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor("#38bdf8"), 2))
            painter.drawRoundedRect(4, 4, 152, 152, 10, 10)
            painter.setPen(QColor("#00f2fe"))
            painter.setFont(QFont("Segoe UI", 48, QFont.Weight.Bold))
            painter.drawText(QRectF(0, 0, 160, 160), Qt.AlignmentFlag.AlignCenter, "❓")
            painter.end()

            self.imageLabel.setPixmap(m_pix)
            self.imageLabel.setCursor(Qt.CursorShape.PointingHandCursor)
            self.imageLabel.mousePressEvent = lambda e: self.onRevealMysteryGame()
            self.gameTitleLabel.mousePressEvent = lambda e: self.onRevealMysteryGame()

            if hasattr(self, 'btnMysteryMode'):
                self.btnMysteryMode.setChecked(True)
                self.btnMysteryMode.setText("👁️ Revelar Jogo")

            update_overlay_game("❓ Jogo Misterioso", "???", "??h")
            return

        # Normal / Revealed Display
        self.gameTitleLabel.setText(display_name)
        self.gameTitleLabel.setCursor(Qt.CursorShape.ArrowCursor)
        self.imageLabel.setCursor(Qt.CursorShape.ArrowCursor)
        self.imageLabel.mousePressEvent = None
        self.gameTitleLabel.mousePressEvent = None

        if hasattr(self, 'btnMysteryMode'):
            self.btnMysteryMode.setChecked(False)
            self.btnMysteryMode.setText("🕵️ Misterioso")

        self.platformBadge.setText(platform.upper())
        self.platformBadge.setStyleSheet(
            f"background-color: {getPlatformColor(platform)}; color: #ffffff; "
            f"border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;"
        )

        # HowLongToBeat Integration (Zero-freeze: instant cache + async background worker)
        overlay_hltb = "--"
        def _apply_hltb_ui(data):
            if data and data.get("main_story", 0) > 0:
                hours = data.get("main_story", 0)
                dur_str = format_hltb_duration(hours)
                self.hltbBadge.setText(dur_str)
                self.hltbBadge.setStyleSheet(get_duration_badge_style(hours))
                self.hltbBadge.setToolTip(
                    f"Campanha Principal: {hours:.1f}h\n"
                    f"História + Extras: {data.get('main_extra', 0):.1f}h\n"
                    f"Complecionista (100%): {data.get('completionist', 0):.1f}h"
                )
                update_overlay_game(display_name, platform, f"~{hours:.1f}h")
            else:
                self.hltbBadge.setText("⏱️ HLTB: --")
                self.hltbBadge.setStyleSheet("background-color: #334155; color: #94a3b8; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;")
                self.hltbBadge.setToolTip("Tempo não catalogado no HowLongToBeat")
                update_overlay_game(display_name, platform, "--")

        try:
            hltb_info = get_cached_hltb(display_name)
            if hltb_info is not None:
                _apply_hltb_ui(hltb_info)
                if hltb_info.get("main_story", 0) > 0:
                    overlay_hltb = f"~{hltb_info.get('main_story', 0):.1f}h"
            else:
                # Fast asynchronous background fetch - never freeze GUI thread
                self.hltbBadge.setText("⏱️ HLTB: ...")
                self.hltbBadge.setStyleSheet("background-color: #1e293b; color: #38bdf8; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;")
                self.hltbBadge.setToolTip("Consultando estimativa no HowLongToBeat em segundo plano...")
                overlay_hltb = "--"

                def _fetch_bg(target_entry, target_name):
                    try:
                        res = fetch_hltb_data(target_name)
                        def _update_if_current():
                            if getattr(self, 'currentChoice', None) == target_entry:
                                _apply_hltb_ui(res)
                        QTimer.singleShot(0, _update_if_current)
                    except Exception as ex:
                        logger.debug(f"Async HLTB error: {ex}")

                import threading
                threading.Thread(target=_fetch_bg, args=(gameEntry, display_name), daemon=True).start()
        except Exception as e:
            logger.debug(f"Erro ao obter badge HLTB: {e}")
            overlay_hltb = "--"

        info = findGameInfo(gameEntry)
        times_played = info[2] if info else 0
        finished = info[4] if info else 0
        fav = info[5] if info else 0
        installed = info[6] if (info and len(info) >= 7) else 1

        is_installed = bool(installed)

        status_text = "Zerado ✔" if finished else "Em aberto"
        fav_text = " • ⭐ Favorito" if fav else ""
        inst_text = " • ✔ Instalado" if is_installed else " • ⏳ Não Instalado"
        self.gameStatsLabel.setText(f"Vezes jogado: {times_played}x • Status: {status_text}{fav_text}{inst_text}")

        self.btnFavorite.setText("⭐ Desfavoritar" if fav else "⭐ Favoritar")
        self.btnFinish.setText("✔ Desmarcar Zerado" if finished else "✔ Marcar Zerado")

        if hasattr(self, 'installBadge'):
            if is_installed:
                self.installBadge.setText("✔ INSTALADO")
                self.installBadge.setStyleSheet(
                    "background-color: #00b894; color: #ffffff; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;"
                )
            else:
                self.installBadge.setText("⏳ NÃO INSTALADO")
                self.installBadge.setStyleSheet(
                    "background-color: #6c5ce7; color: #ffffff; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;"
                )

        if is_installed:
            self.btnPlay.setText("▶  JOGAR AGORA")
            self.btnPlay.setStyleSheet("""
                QPushButton#BtnPlay {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00b894, stop:1 #00cec9);
                    color: #0d0f14;
                    font-size: 14px;
                    font-weight: bold;
                    border: none;
                    border-radius: 8px;
                    padding: 12px;
                }
                QPushButton#BtnPlay:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #55efc4, stop:1 #81ecec);
                }
            """)
        else:
            self.btnPlay.setText("📥  INSTALAR JOGO")
            self.btnPlay.setStyleSheet("""
                QPushButton#BtnPlay {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6c5ce7, stop:1 #a29bfe);
                    color: #ffffff;
                    font-size: 14px;
                    font-weight: bold;
                    border: none;
                    border-radius: 8px;
                    padding: 12px;
                }
                QPushButton#BtnPlay:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a29bfe, stop:1 #dfe6e9);
                    color: #0d0f14;
                }
            """)

        # Load Icon
        try:
            pilImg = findGameIcon(
                gameEntry,
                playnitePath=getattr(self.config, 'playnitePath', '')
            )
            pilImg = pilImg.convert("RGBA")
            data = pilImg.tobytes("raw", "RGBA")
            qim = QImage(data, pilImg.size[0], pilImg.size[1], QImage.Format.Format_RGBA8888)
            cover_w = getattr(self.config, 'uiCoverWidth', 160)
            cover_h = getattr(self.config, 'uiCoverHeight', 160)
            pix = QPixmap.fromImage(qim).scaled(cover_w, cover_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.imageLabel.setPixmap(pix)
            if self.overlayWindow and self.overlayWindow.isVisible():
                self.overlayWindow.updateGame(display_name, pix, platform)
            
            # Broadcast to OBS Web Overlay
            update_overlay_game(display_name, platform, overlay_hltb)
        except Exception as e:
            logger.warning(f"Error rendering icon in dashboard: {e}")

    # -------------------------------------------------------------
    # Logics & Updates: Game of the Day (GOTD)
    # -------------------------------------------------------------
    def onRerollGotd(self, initial=False):
        chosen = getGameOfTheDay(self.content, seed_date=initial)
        if not chosen:
            chosen = self.currentChoice
        self.currentGotd = chosen
        self.updateGotdDisplay(chosen)

    def updateGotdDisplay(self, gameEntry):
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
            self.btnGotdPlay.setText("▶  JOGAR JOGO DO DIA AGORA")
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
            pilImg = findGameIcon(
                gameEntry,
                playnitePath=getattr(self.config, 'playnitePath', '')
            )
            pilImg = pilImg.convert("RGBA")
            data = pilImg.tobytes("raw", "RGBA")
            qim = QImage(data, pilImg.size[0], pilImg.size[1], QImage.Format.Format_RGBA8888)
            pix = QPixmap.fromImage(qim).scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.gotdImageLabel.setPixmap(pix)
        except Exception as e:
            logger.warning(f"Error rendering GOTD icon: {e}")

    def onPlayGotd(self):
        target = self.currentGotd or self.currentChoice
        info = findGameInfo(target)
        is_installed = (info[6] == 1) if (info and len(info) >= 7) else 1

        if is_installed:
            logger.info(f"Launching Game of the Day: {target}")
            self.startGameplaySession(target)
            self.showMinimized()
            executeGame(target, self.steamOwnedGames)
        else:
            logger.info(f"Installing Game of the Day: {target}")
            success = installGame(target)
            if success:
                QMessageBox.information(self, "Instalação", f"Comando de instalação acionado para:\n{formatDisplayName(target)}")
            else:
                QMessageBox.warning(self, "Instalação", f"Não foi possível disparar instalador automaticamente para:\n{formatDisplayName(target)}")

        self.refreshStats()
        self.refreshTable()
        if self.currentGotd:
            self.updateGotdDisplay(self.currentGotd)

    # -------------------------------------------------------------
    # Logics & Updates: Game of the Year (GOTY)
    # -------------------------------------------------------------
    def onRerollGoty(self):
        goty = getRandomGoty()
        if not goty:
            return
        self.currentGoty = goty
        self.updateGotyDisplay(goty)

    def updateGotyDisplay(self, goty):
        self.gotyYearBadge.setText(f"🏆 GAME OF THE YEAR - ANO {goty['year']}")
        self.gotyTitleLabel.setText(goty['title'])
        self.gotyMetaLabel.setText(f"{goty['developer']} • {goty['genre']} • {goty['awards']}")
        self.gotySummaryLabel.setText(goty['summary'])

        is_inst = goty['is_installed']
        if is_inst:
            self.gotyInstalledBadge.setText("✔ INSTALADO NO SEU PC")
            self.gotyInstalledBadge.setStyleSheet("background-color: #00b894; color: #0d0f14; border-radius: 6px; padding: 4px 10px; font-weight: bold;")
            self.btnGotyPlay.setEnabled(True)
            self.btnGotyPlay.setText("▶  JOGAR GOTY INSTALADO")
            self.btnGotyPlay.setStyleSheet("")
        else:
            self.gotyInstalledBadge.setText("NÃO INSTALADO")
            self.gotyInstalledBadge.setStyleSheet("background-color: #2d3748; color: #a0aec0; border-radius: 6px; padding: 4px 10px; font-weight: bold;")
            self.btnGotyPlay.setEnabled(False)
            self.btnGotyPlay.setText("🔒 Não Instalado no PC")
            self.btnGotyPlay.setStyleSheet("background-color: #2d3748; color: #718096;")

        # Resolve Cover Art
        try:
            lookup_target = goty.get('library_entry') if goty.get('is_installed') and goty.get('library_entry') else goty['title']
            pilImg = findGameIcon(
                lookup_target,
                playnitePath=getattr(self.config, 'playnitePath', '')
            )
            pilImg = pilImg.convert("RGBA")
            data = pilImg.tobytes("raw", "RGBA")
            qim = QImage(data, pilImg.size[0], pilImg.size[1], QImage.Format.Format_RGBA8888)
            pix = QPixmap.fromImage(qim).scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.gotyImageLabel.setPixmap(pix)
        except Exception as e:
            logger.warning(f"Error rendering GOTY cover: {e}")

    def onPlayGoty(self):
        if not self.currentGoty or not self.currentGoty.get('is_installed'):
            return
        target = self.currentGoty.get('library_entry')
        if target:
            logger.info(f"Launching GOTY game: {target}")
            self.startGameplaySession(target)
            self.showMinimized()
            executeGame(target, self.steamOwnedGames)
            self.refreshStats()
            self.refreshTable()

    def onExploreGoty(self):
        if not self.currentGoty:
            return
        title = self.currentGoty['title']
        url = f"https://www.google.com/search?q={title.replace(' ', '+')}+game"
        webbrowser.open(url)

    def refreshGotyTable(self):
        gotys = getAllGotys()
        query = self.gotySearchBox.text().strip().lower()
        if query:
            gotys = [g for g in gotys if query in g['title'].lower() or query in str(g['year']) or query in g['developer'].lower()]

        self.gotyTable.setRowCount(len(gotys))
        for row, g in enumerate(gotys):
            yearItem = QTableWidgetItem(str(g['year']))
            yearItem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            yearItem.setForeground(QColor("#d4af37"))

            titleItem = QTableWidgetItem(g['title'])
            titleItem.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            titleItem.setData(Qt.ItemDataRole.UserRole, g)

            devItem = QTableWidgetItem(g['developer'])
            genreItem = QTableWidgetItem(g['genre'])
            awardsItem = QTableWidgetItem(g['awards'])
            awardsItem.setForeground(QColor("#a0aec0"))

            instText = "✔ Sim" if g['is_installed'] else "—"
            instItem = QTableWidgetItem(instText)
            instItem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if g['is_installed']:
                instItem.setForeground(QColor("#00cec9"))
            else:
                instItem.setForeground(QColor("#718096"))

            self.gotyTable.setItem(row, 0, yearItem)
            self.gotyTable.setItem(row, 1, titleItem)
            self.gotyTable.setItem(row, 2, devItem)
            self.gotyTable.setItem(row, 3, genreItem)
            self.gotyTable.setItem(row, 4, awardsItem)
            self.gotyTable.setItem(row, 5, instItem)

    def onGotySearchChanged(self, text):
        self.refreshGotyTable()

    def onGotyTableDoubleClicked(self, index):
        row = self.gotyTable.currentRow()
        if row >= 0:
            item = self.gotyTable.item(row, 1)
            if item:
                goty = item.data(Qt.ItemDataRole.UserRole)
                if goty:
                    self.currentGoty = goty
                    self.updateGotyDisplay(goty)
                    if goty['is_installed'] and goty.get('library_entry'):
                        self.onPlayGoty()

    # -------------------------------------------------------------
    # General Event Handlers
    # -------------------------------------------------------------
    def refreshStats(self):
        stats = getDatabaseStats()
        total = stats["total_games"]
        installed = stats.get("installed_count", total)
        played = stats["total_played"]
        finished = stats["finished_count"]
        rate = stats["completion_rate"]

        self.statTotal.findChild(QLabel, "StatValue").setText(f"{total:,}".replace(",", "."))
        if hasattr(self, 'statInstalled'):
            self.statInstalled.findChild(QLabel, "StatValue").setText(f"{installed:,}".replace(",", "."))
        self.statPlayed.findChild(QLabel, "StatValue").setText(str(played))
        self.statFinished.findChild(QLabel, "StatValue").setText(str(finished))
        self.statBacklog.findChild(QLabel, "StatValue").setText(f"{rate}%")

    def refreshTable(self):
        query = self.searchBox.text().strip()
        status_filter = self.filterCombo.currentText()
        limit = getattr(self.config, 'uiTableLimit', 400)
        rows = getGamesList(filterText=query, statusFilter=status_filter, limit=limit)
        
        self.table.setRowCount(len(rows))
        for row_idx, r in enumerate(rows):
            game_name = r[1]
            times_played = r[2] or 0
            last_played = r[3] or "Nunca"
            finished = r[4] or 0
            favorite = r[5] or 0
            installed = r[6] if len(r) >= 7 else 1

            display_title = formatDisplayName(game_name)
            platform = detectPlatform(game_name)

            titleItem = QTableWidgetItem(f"{'⭐ ' if favorite else ''}{display_title}")
            titleItem.setData(Qt.ItemDataRole.UserRole, game_name)
            titleItem.setData(Qt.ItemDataRole.UserRole + 1, installed)
            
            platItem = QTableWidgetItem(platform)
            platItem.setForeground(QColor(getPlatformColor(platform)))

            installedItem = QTableWidgetItem("✔ Sim" if installed else "⏳ Não")
            installedItem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if installed:
                installedItem.setForeground(QColor("#00b894"))
            else:
                installedItem.setForeground(QColor("#a29bfe"))

            timesItem = QTableWidgetItem(f"{times_played}x")
            timesItem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            lastItem = QTableWidgetItem(str(last_played).split(".")[0])
            
            statusItem = QTableWidgetItem("✔ Zerado" if finished else "Em aberto")
            if finished:
                statusItem.setForeground(QColor("#00b894"))
            else:
                statusItem.setForeground(QColor("#8c96a8"))

            self.table.setItem(row_idx, 0, titleItem)
            self.table.setItem(row_idx, 1, platItem)
            self.table.setItem(row_idx, 2, installedItem)
            self.table.setItem(row_idx, 3, timesItem)
            self.table.setItem(row_idx, 4, lastItem)
            self.table.setItem(row_idx, 5, statusItem)

    def onSearchChanged(self, text):
        self._searchTimer.start(250)

    def onFilterChanged(self, idx):
        self.refreshTable()

    def onTableSelectionChanged(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                is_installed = item.data(Qt.ItemDataRole.UserRole + 1)
                if is_installed is None:
                    target = item.data(Qt.ItemDataRole.UserRole)
                    info = findGameInfo(target)
                    is_installed = (info[6] == 1) if (info and len(info) >= 7) else 1
                if is_installed:
                    self.btnPlaySelected.setText("▶ Jogar Selecionado")
                else:
                    self.btnPlaySelected.setText("📥 Instalar Selecionado")

    def onRerollHero(self):
        filter_mode = self.comboRerollFilter.currentText()
        filtered_content = self.content

        if "Apenas Instalados" in filter_mode:
            inst_names = getInstalledGamesSet()
            filtered_content = [g for g in self.content if g in inst_names]
            if not filtered_content and inst_names:
                filtered_content = list(inst_names)
        elif "Apenas Não Instalados" in filter_mode:
            uninst_names = getUninstalledGamesSet()
            filtered_content = [g for g in self.content if g in uninst_names]
            if not filtered_content and uninst_names:
                filtered_content = list(uninst_names)
        elif "Favoritos" in filter_mode:
            fav_names = getFavoriteGamesSet()
            filtered_content = [g for g in self.content if g in fav_names]
            if not filtered_content and fav_names:
                filtered_content = list(fav_names)
        elif "eXoDOS" in filter_mode:
            filtered_content = [g for g in self.content if g.startswith(exodosPrefix) or "exodos" in g.lower()]
        elif "Atalhos" in filter_mode:
            filtered_content = [g for g in self.content if g.startswith(linkPrefix)]
        elif "Locais" in filter_mode:
            filtered_content = [g for g in self.content if not g.startswith(linkPrefix) and not g.startswith(exodosPrefix) and not g.startswith(PLAYNITE_PREFIX)]
        elif "Emuladores" in filter_mode or "Consoles" in filter_mode:
            all_known_stores = {
                "Steam", "GOG", "Epic", "Epic Games", "Xbox", "Amazon", 
                "Amazon Games", "Ubisoft", "EA app", "Battle.net", "Riot Games", 
                "eXoDOS", "DOSBox", "Atalho / Desktop", "Instalação Local", "Playnite"
            }
            filtered_content = [
                g for g in self.content 
                if g.startswith(PLAYNITE_PREFIX) and detectPlatform(g) not in all_known_stores
            ]
            if not filtered_content:
                try:
                    from aesgard.playnite import loadPlayniteGames, formatPlayniteEntries
                    pn_path = getattr(self.config, 'playnitePath', '')
                    pn_games = loadPlayniteGames(pn_path, onlyInstalled=False)
                    if pn_games:
                        pn_entries = formatPlayniteEntries(pn_games)
                        for entry in pn_entries:
                            if entry not in self.content:
                                self.content.append(entry)
                        filtered_content = [
                            g for g in pn_entries
                            if detectPlatform(g) not in all_known_stores
                        ]
                        logger.info(f"Carregados {len(filtered_content)} jogos de emuladores do Playnite sob demanda.")
                except Exception as e:
                    logger.warning(f"Erro ao carregar jogos de emuladores sob demanda: {e}")
        elif "Curtos" in filter_mode: # < 5h
            preload_hltb_cache()
            all_durations = get_all_cached_durations()
            short_cands = []
            for g in self.content:
                clean = clean_title_for_hltb(formatDisplayName(g)).lower()
                dur = all_durations.get(clean, 0.0)
                if not dur and ":" in clean:
                    dur = all_durations.get(clean.split(":")[0].strip(), 0.0)
                if 0 < dur < 5.0:
                    short_cands.append(g)

            if len(short_cands) >= 5:
                filtered_content = short_cands
            else:
                # Fast smart fallback: Retro, Arcade, DOS games are historically short (< 5h)
                retro_platforms = {"eXoDOS", "DOSBox", "NES", "SNES", "Arcade", "MAME", "Master System", "Mega Drive", "Game Boy", "Game Boy Advance", "Atari"}
                retro_cands = [
                    g for g in self.content 
                    if detectPlatform(g) in retro_platforms or g.startswith(exodosPrefix) or "[eXoDOS]" in g
                ]
                candidate_pool = list(dict.fromkeys(short_cands + retro_cands))
                filtered_content = candidate_pool if candidate_pool else self.content
        elif "Médios" in filter_mode: # 5-15h
            preload_hltb_cache()
            all_durations = get_all_cached_durations()
            med_cands = []
            for g in self.content:
                clean = clean_title_for_hltb(formatDisplayName(g)).lower()
                dur = all_durations.get(clean, 0.0)
                if not dur and ":" in clean:
                    dur = all_durations.get(clean.split(":")[0].strip(), 0.0)
                if 5.0 <= dur <= 15.0:
                    med_cands.append(g)

            if med_cands:
                filtered_content = med_cands
            else:
                filtered_content = [g for g in self.content if not g.startswith(exodosPrefix)] or self.content
        elif "Longos" in filter_mode: # > 25h
            preload_hltb_cache()
            all_durations = get_all_cached_durations()
            long_cands = []
            for g in self.content:
                clean = clean_title_for_hltb(formatDisplayName(g)).lower()
                dur = all_durations.get(clean, 0.0)
                if not dur and ":" in clean:
                    dur = all_durations.get(clean.split(":")[0].strip(), 0.0)
                if dur > 25.0:
                    long_cands.append(g)

            if long_cands:
                filtered_content = long_cands
            else:
                rpg_keywords = {"rpg", "witcher", "scrolls", "fallout", "souls", "fantasy", "dragon", "divinity", "crusader", "civilization", "persona", "quest", "chronicles", "tactics", "ogre"}
                rpg_cands = [
                    g for g in self.content 
                    if any(kw in g.lower() for kw in rpg_keywords)
                ]
                filtered_content = rpg_cands or self.content
        elif "Playnite" in filter_mode:
            filtered_content = [
                g for g in self.content 
                if g.startswith(PLAYNITE_PREFIX) or g.startswith("steam:") or g.startswith("gog:") or "steam" in g.lower() or "gog" in g.lower() or "epic" in g.lower()
            ]
            if not filtered_content:
                try:
                    from aesgard.playnite import loadPlayniteGames, formatPlayniteEntries
                    pn_path = getattr(self.config, 'playnitePath', '')
                    pn_games = loadPlayniteGames(pn_path, onlyInstalled=False)
                    if pn_games:
                        pn_entries = formatPlayniteEntries(pn_games)
                        for entry in pn_entries:
                            if entry not in self.content:
                                self.content.append(entry)
                        filtered_content = pn_entries
                        logger.info(f"Carregados {len(pn_entries)} jogos do Playnite sob demanda.")
                except Exception as e:
                    logger.warning(f"Erro ao carregar jogos do Playnite sob demanda: {e}")

        if not filtered_content:
            QMessageBox.information(
                self, 
                "Aviso", 
                f"Nenhum jogo encontrado para a categoria: {filter_mode}.\n\n"
                "Alternando para 'Todas as Fontes' para continuar o sorteio."
            )
            self.comboRerollFilter.blockSignals(True)
            self.comboRerollFilter.setCurrentIndex(0)
            self.comboRerollFilter.blockSignals(False)
            filtered_content = self.content

        if not filtered_content:
            return

        def do_pick():
            new_choice = chooseGame(filtered_content, sampleSize=getattr(self.config, 'randomSampleSize', 25))
            self.updateHeroDisplay(new_choice)

        if hasattr(self, 'chkRoulette') and self.chkRoulette.isChecked():
            self.startRouletteAnimation(do_pick)
        else:
            do_pick()

    def onCleanDatabase(self):
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("Limpeza de Banco de Dados")
        msgBox.setIcon(QMessageBox.Icon.Question)
        msgBox.setTextFormat(Qt.TextFormat.RichText)
        msgBox.setText(
            "<b>Deseja iniciar a verificação de integridade do banco de dados agora?</b><br><br>"
            "Esta rotina irá verificar quais jogos cadastrados no banco estão instalados atualmente no seu computador.<br><br>"
            "• Jogos que não forem encontrados serão marcados como <b>NÃO INSTALADOS</b>.<br>"
            "• <font color='#00cec9'><b>Nenhum registro é deletado: contadores de jogatinas, datas e favoritos continuam preservados com segurança!</b></font><br>"
            "• <font color='#00cec9'><b>Nenhum arquivo do seu computador será apagado</b></font>.<br>"
            "• Pastas residuais serão listadas no relatório final."
        )
        msgBox.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msgBox.setDefaultButton(QMessageBox.StandardButton.No)
        
        reply = msgBox.exec()
        if reply != QMessageBox.StandardButton.Yes:
            return

        from aesgard.database import cleanOrphanGames, opencon
        from aesgard.gameutil import isGameInstalledOnSystem

        playnite_ids = set()
        if getattr(self.config, 'playniteEnabled', True):
            for entry in self.content:
                if entry.startswith(PLAYNITE_PREFIX):
                    parts = entry.split(":")
                    if len(parts) >= 3:
                        playnite_ids.add(parts[-1])

        def check_func(game_name):
            return isGameInstalledOnSystem(game_name, self.config, playniteInstalledIds=playnite_ids)

        progress = QProgressDialog("Iniciando verificação do banco de dados...", "Cancelar", 0, 100, self)
        progress.setWindowTitle("Verificando Instalações")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        def on_progress(current, total):
            if total > 0:
                pct = int((current / total) * 100)
                progress.setValue(pct)
                progress.setLabelText(f"Verificando jogos instalados ({current:,} / {total:,})...".replace(",", "."))
            QApplication.processEvents()

        try:
            conn = opencon()
            result = cleanOrphanGames(conn, self.config, check_installed_func=check_func, progress_callback=on_progress)
            conn.close()
            progress.setValue(100)
            self.refreshStats()
            self.refreshTable()
            self.updateHeroDisplay(self.currentChoice)
        except Exception as e:
            logger.error(f"Erro durante limpeza: {e}")
            result = {"total_checked": 0, "removed_count": 0, "warnings_not_empty": [str(e)]}
        finally:
            progress.close()

        resBox = QMessageBox(self)
        resBox.setWindowTitle("Relatório de Verificação")
        resBox.setTextFormat(Qt.TextFormat.RichText)
        msg = (
            f"<b>Verificação concluída com sucesso!</b><br><br>"
            f"• Jogos verificados: <b>{result['total_checked']:,}</b><br>".replace(",", ".") +
            f"• Jogos atualizados para NÃO INSTALADOS: <font color='#fdcb6e'><b>{result['removed_count']:,}</b></font><br>".replace(",", ".") +
            f"<i>(Seus históricos de jogo e favoritos foram mantidos intactos)</i><br>"
        )

        if result["warnings_not_empty"]:
            msg += "<br><font color='#fdcb6e'><b>⚠️ Pastas com arquivos residuais (jogo não instalado):</b></font><br>"
            msg += "<div style='font-size: 11px; max-height: 180px; overflow-y: scroll;'><ul>"
            for w in result["warnings_not_empty"][:30]:
                msg += f"<li>{w}</li>"
            if len(result["warnings_not_empty"]) > 30:
                msg += f"<li><i>...e mais {len(result['warnings_not_empty']) - 30} pastas com arquivos.</i></li>"
            msg += "</ul></div>"

        resBox.setText(msg)
        resBox.setIcon(QMessageBox.Icon.Information)
        resBox.exec()

    def onSyncSources(self):
        progress = QProgressDialog("Escaneando todas as fontes de jogos...", None, 0, 0, self)
        progress.setWindowTitle("Sincronizando Fontes")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        QApplication.processEvents()

        try:
            clearPlayniteMetaCache()
            scanned = scanAllSources(self.config, includeUninstalled=True)
            stats_import = importContentToDatabase(scanned)
            self.content = [entry for entry, _ in scanned]
            self.refreshStats()
            self.refreshTable()
            self.updateHeroDisplay(self.currentChoice)

            installed_total = sum(1 for _, inst in scanned if inst == 1)
            uninstalled_total = sum(1 for _, inst in scanned if inst == 0)

            QMessageBox.information(
                self,
                "Sincronização Concluída",
                f"<b>Catálogo de jogos sincronizado com sucesso!</b><br><br>"
                f"• Total de jogos identificados: <b>{len(scanned):,}</b><br>"
                f"• Jogos instalados: <font color='#00cec9'><b>{installed_total:,}</b></font><br>"
                f"• Jogos não instalados: <font color='#a29bfe'><b>{uninstalled_total:,}</b></font><br><br>"
                f"<i>O banco de dados foi atualizado. Jogos instalados podem ser jogados imediatamente e jogos não instalados possuem botão de instalação.</i>".replace(",", ".")
            )
        except Exception as e:
            logger.error(f"Erro ao sincronizar fontes: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro de Sincronização", f"Ocorreu um erro ao sincronizar as fontes:\n{e}")
        finally:
            progress.close()

    def onPlayHero(self):
        target = self.currentChoice
        info = findGameInfo(target)
        is_installed = (info[6] == 1) if (info and len(info) >= 7) else 1

        if is_installed:
            logger.info(f"Launching game from Hero Card: {target}")
            self.startGameplaySession(target)
            self.showMinimized()
            executeGame(target, self.steamOwnedGames)
        else:
            logger.info(f"Installing uninstalled game from Hero Card: {target}")
            success = installGame(target)
            if success:
                QMessageBox.information(
                    self,
                    "Instalação Acionada",
                    f"A instalação/preparação do jogo foi acionada:<br><br><b>{formatDisplayName(target)}</b>"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Instalação",
                    f"Não foi possível disparar o instalador automaticamente para:<br><br><b>{formatDisplayName(target)}</b><br><br>"
                    f"Verifique se o cliente correspondente (Playnite/Steam/eXoDOS) está instalado e configurado."
                )

        self.refreshStats()
        self.refreshTable()
        self.updateHeroDisplay(self.currentChoice)

    def onPlaySelected(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                target = item.data(Qt.ItemDataRole.UserRole)
                info = findGameInfo(target)
                is_installed = (info[6] == 1) if (info and len(info) >= 7) else 1

                if is_installed:
                    logger.info(f"Launching game from Database Table: {target}")
                    self.startGameplaySession(target)
                    self.showMinimized()
                    executeGame(target, self.steamOwnedGames)
                else:
                    logger.info(f"Installing uninstalled game from Database Table: {target}")
                    success = installGame(target)
                    if success:
                        QMessageBox.information(
                            self,
                            "Instalação Acionada",
                            f"A instalação/preparação do jogo foi acionada:<br><br><b>{formatDisplayName(target)}</b>"
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "Instalação",
                            f"Não foi possível disparar o instalador automaticamente para:<br><br><b>{formatDisplayName(target)}</b>"
                        )

                self.refreshStats()
                self.refreshTable()
                self.updateHeroDisplay(target)
        else:
            QMessageBox.information(self, "Aviso", "Por favor, selecione um jogo na tabela primeiro.")

    def onTableDoubleClicked(self, index):
        self.onPlaySelected()

    def onToggleFavorite(self):
        info = findGameInfo(self.currentChoice)
        current_fav = info[5] if info else 0
        new_fav = 0 if current_fav else 1
        setFavorite(self.currentChoice, new_fav)
        self.updateHeroDisplay(self.currentChoice)
        self.refreshStats()
        self.refreshTable()

    def onToggleFinished(self):
        info = findGameInfo(self.currentChoice)
        current_fin = info[4] if info else 0
        new_fin = 0 if current_fin else 1
        setFinished(self.currentChoice, new_fin)
        self.updateHeroDisplay(self.currentChoice)
        self.refreshStats()
        self.refreshTable()

    # -------------------------------------------------------------
    # Streamer, Roleta & Live Intelligence Methods
    # -------------------------------------------------------------
    def startRouletteAnimation(self, on_finished_callback):
        if hasattr(self, '_rouletteTimer') and self._rouletteTimer and self._rouletteTimer.isActive():
            return
        
        self._rouletteTicks = 0
        self._rouletteTotalTicks = 16
        self._rouletteInterval = 60
        self._rouletteCallback = on_finished_callback
        self.btnReroll.setEnabled(False)

        self._rouletteTimer = QTimer(self)
        self._rouletteTimer.timeout.connect(self._onRouletteTick)
        self._rouletteTimer.start(self._rouletteInterval)

    def _onRouletteTick(self):
        self._rouletteTicks += 1
        if self.content:
            cand = random.choice(self.content)
            self.gameTitleLabel.setText(f"🎲 {formatDisplayName(cand)}...")
            self.platformBadge.setText("SORTEANDO...")
            self.platformBadge.setStyleSheet("background-color: #6c5ce7; color: #ffffff; border-radius: 6px; padding: 3px 8px; font-weight: bold;")

        if self._rouletteTicks > 8:
            self._rouletteInterval = int(self._rouletteInterval * 1.25)
            self._rouletteTimer.setInterval(self._rouletteInterval)

        if self._rouletteTicks >= self._rouletteTotalTicks:
            self._rouletteTimer.stop()
            self.btnReroll.setEnabled(True)
            if self._rouletteCallback:
                self._rouletteCallback()

    def onApplyLiveTheme(self, mode):
        if mode == "all":
            self.comboRerollFilter.setCurrentIndex(0)
        elif mode == "emulators":
            idx = self.comboRerollFilter.findText("Emuladores", Qt.MatchFlag.MatchContains)
            if idx >= 0:
                self.comboRerollFilter.setCurrentIndex(idx)
        elif mode == "retro":
            idx = self.comboRerollFilter.findText("eXoDOS", Qt.MatchFlag.MatchContains)
            if idx >= 0:
                self.comboRerollFilter.setCurrentIndex(idx)
        elif mode == "modern":
            idx = self.comboRerollFilter.findText("Playnite", Qt.MatchFlag.MatchContains)
            if idx >= 0:
                self.comboRerollFilter.setCurrentIndex(idx)
        elif mode == "favorites":
            idx = self.comboRerollFilter.findText("Favoritos", Qt.MatchFlag.MatchContains)
            if idx >= 0:
                self.comboRerollFilter.setCurrentIndex(idx)
            else:
                self.onRerollHero()
            return
        elif mode == "backlog":
            played_names = getPlayedGamesSet()
            zeros = [g for g in self.content if g not in played_names]
            if zeros:
                new_choice = chooseGame(zeros, sampleSize=getattr(self.config, 'randomSampleSize', 25))
                if self.chkRoulette.isChecked():
                    self.startRouletteAnimation(lambda: self.updateHeroDisplay(new_choice))
                else:
                    self.updateHeroDisplay(new_choice)
            else:
                QMessageBox.information(self, "Tema da Live", "Parabéns! Todos os jogos já foram jogados pelo menos uma vez.")
            return

        self.onRerollHero()

    def onOpenHeroIntel(self):
        pix = self.imageLabel.pixmap()
        dlg = GameIntelDialog(self.currentChoice, coverPixmap=pix, parent=self)
        dlg.exec()

    def onOpenGotdIntel(self):
        target = self.currentGotd or self.currentChoice
        pix = self.gotdImageLabel.pixmap()
        dlg = GameIntelDialog(target, coverPixmap=pix, parent=self)
        dlg.exec()

    def onOpenGotyIntel(self):
        title = self.currentGoty['title'] if self.currentGoty else "GOTY"
        pix = self.gotyImageLabel.pixmap()
        dlg = GameIntelDialog(title, coverPixmap=pix, parent=self)
        dlg.exec()

    def onOpenObsOverlay(self):
        if not self.overlayWindow or not self.overlayWindow.isVisible():
            pix = self.imageLabel.pixmap()
            platform = detectPlatform(self.currentChoice)
            self.overlayWindow = StreamerOverlayWindow(
                gameTitle=formatDisplayName(self.currentChoice),
                coverPixmap=pix,
                platformText=platform
            )
            self.overlayWindow.show()
        else:
            self.overlayWindow.activateWindow()

    # -------------------------------------------------------------
    # Chat Choice Trio Handlers
    # -------------------------------------------------------------
    def onRerollChatChoice(self):
        if len(self.content) < 3:
            candidates = self.content * 3
        else:
            candidates = random.sample(self.content, 3)

        self.chatChoiceTrio = candidates
        self.chatVotes = [0, 0, 0]

        names = [formatDisplayName(g) for g in candidates]
        update_overlay_poll(names[0], names[1], names[2], 0, 0, 0)

        for i, game in enumerate(candidates):
            card_info = self.trioCards[i]
            card_info["gameEntry"] = game
            card_info["titleLabel"].setText(formatDisplayName(game))
            plat = detectPlatform(game)
            card_info["metaLabel"].setText(f"Plataforma: {plat}")
            if "lblVoteCount" in card_info:
                card_info["lblVoteCount"].setText("0 votos (0%)")

            try:
                pilImg = findGameIcon(game, playnitePath=getattr(self.config, 'playnitePath', ''))
                pilImg = pilImg.convert("RGBA")
                data = pilImg.tobytes("raw", "RGBA")
                qim = QImage(data, pilImg.size[0], pilImg.size[1], QImage.Format.Format_RGBA8888)
                pix = QPixmap.fromImage(qim).scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                card_info["coverLabel"].setPixmap(pix)
            except Exception:
                pass

    def onAddChatVote(self, index):
        if 0 <= index < len(self.chatVotes):
            self.chatVotes[index] += 1
            total_votes = sum(self.chatVotes)
            for i, card_info in enumerate(self.trioCards):
                v = self.chatVotes[i]
                pct = int((v / total_votes) * 100) if total_votes > 0 else 0
                if "lblVoteCount" in card_info:
                    card_info["lblVoteCount"].setText(f"{v} votos ({pct}%)")

            names = [formatDisplayName(g) for g in self.chatChoiceTrio] if len(self.chatChoiceTrio) >= 3 else ["A", "B", "C"]
            update_overlay_poll(
                names[0], names[1], names[2],
                self.chatVotes[0], self.chatVotes[1], self.chatVotes[2]
            )

    def onPlayChatChoice(self, index):
        if 0 <= index < len(self.chatChoiceTrio):
            target = self.chatChoiceTrio[index]
            logger.info(f"Launching winning Chat Choice game: {target}")
            self.startGameplaySession(target)
            self.showMinimized()
            executeGame(target, self.steamOwnedGames)
            self.refreshStats()
            self.refreshTable()
            self.updateHeroDisplay(target)

    def onOpenChatChoiceIntel(self, index):
        if 0 <= index < len(self.chatChoiceTrio):
            target = self.chatChoiceTrio[index]
            pix = self.trioCards[index]["coverLabel"].pixmap()
            dlg = GameIntelDialog(target, coverPixmap=pix, parent=self)
            dlg.exec()

    def onCopyChatPoll(self):
        if len(self.chatChoiceTrio) < 3:
            return
        names = [formatDisplayName(g) for g in self.chatChoiceTrio]
        poll_text = f"🎮 ENQUETE DA LIVE - QUAL DEVO JOGAR HOJE?\n\nOpção A: {names[0]}\nOpção B: {names[1]}\nOpção C: {names[2]}\n\nVotem no chat!"
        cb = QApplication.clipboard()
        if cb:
            cb.setText(poll_text)
            QMessageBox.information(self, "Enquete Copiada!", f"Texto da enquete copiado para o Clipboard:\n\n{poll_text}")

    # -------------------------------------------------------------
    # Session Gameplay Timer & Stopwatch
    # -------------------------------------------------------------
    def startGameplaySession(self, gameEntry):
        self.activePlayingGame = gameEntry
        self.sessionStartTime = time.time()
        name = formatDisplayName(gameEntry)
        self.lblSessionGame.setText(name)
        self.lblSessionTime.setText("⏱️ 00:00:00")
        self.sessionBar.show()
        self.sessionTimer.start()
        update_overlay_timer("00:00:00")

    def _onSessionTimerTick(self):
        if not self.sessionStartTime:
            return
        elapsed_sec = int(time.time() - self.sessionStartTime)
        hours = elapsed_sec // 3600
        minutes = (elapsed_sec % 3600) // 60
        seconds = elapsed_sec % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.lblSessionTime.setText(f"⏱️ {time_str}")
        update_overlay_timer(time_str)

    def onStopGameplaySession(self):
        if not self.sessionStartTime or not self.activePlayingGame:
            self.sessionBar.hide()
            return
        
        elapsed_sec = int(time.time() - self.sessionStartTime)
        duration_hours = round(elapsed_sec / 3600.0, 2)
        if duration_hours < 0.01:
            duration_hours = 0.01
        
        minutes = int(elapsed_sec // 60)
        game_name = self.activePlayingGame
        display_name = formatDisplayName(game_name)

        # Stop timer
        self.sessionTimer.stop()
        self.sessionStartTime = None
        self.sessionBar.hide()
        update_overlay_timer("00:00:00")

        # Save to Live History automatically
        self.liveHistoryMgr.recordLive(
            gameName=game_name,
            durationHours=duration_hours,
            notes=f"Sessão de gameplay ({minutes} minutos) finalizada pelo streamer"
        )
        self.refreshLiveHistoryTable()

        QMessageBox.information(
            self,
            "Sessão Finalizada",
            f"<b>Sessão de gameplay gravada com sucesso!</b><br><br>"
            f"• Jogo: <b>{display_name}</b><br>"
            f"• Duração: <font color='#00cec9'><b>{minutes} minutos ({duration_hours}h)</b></font><br><br>"
            f"O registro foi adicionado automaticamente ao seu Histórico de Lives."
        )

    # -------------------------------------------------------------
    # Modo Jogo Misterioso (Blind Pick)
    # -------------------------------------------------------------
    def onToggleMysteryMode(self):
        self.isMysteryMode = not self.isMysteryMode
        self.mysteryRevealed = False
        self.updateHeroDisplay(self.currentChoice)

    def onRevealMysteryGame(self):
        if self.isMysteryMode and not self.mysteryRevealed:
            self.mysteryRevealed = True
            self.updateHeroDisplay(self.currentChoice)

    # -------------------------------------------------------------
    # Roda da Fortuna (Wheel of Fortune)
    # -------------------------------------------------------------
    def onOpenWheelOfFortune(self):
        # Pick 8-12 distinct candidates from current library/filters
        pool = self.content if self.content else [self.currentChoice]
        cands_count = min(12, len(pool))
        cands = random.sample(pool, cands_count) if len(pool) >= cands_count else pool

        dlg = WheelOfFortuneDialog(cands, self)
        if dlg.exec():
            winner = dlg.get_winner()
            if winner:
                self.updateHeroDisplay(winner)
                self.stack.setCurrentIndex(0)
                self.btnNavMain.setChecked(True)

    # -------------------------------------------------------------
    # Social Card Generator (1200x630 PNG)
    # -------------------------------------------------------------
    def onGenerateSocialCard(self):
        pix = self.imageLabel.pixmap()
        liveChannelUrl = getattr(self.config, 'streamerYouTubeLiveChannel', '').strip()
        mainChannelUrl = getattr(self.config, 'streamerYouTubeMainChannel', '').strip()
        handle = extractChannelHandle(liveChannelUrl or mainChannelUrl, "@Hablocher")

        try:
            out_path = generate_live_card(
                self.currentChoice,
                cover_pixmap=pix,
                channel_name=handle,
                custom_tag="🎮 JOGO DA LIVE",
                out_dir="screenshots"
            )

            msgBox = QMessageBox(self)
            msgBox.setWindowTitle("Card Social Gerado!")
            msgBox.setIcon(QMessageBox.Icon.Information)
            msgBox.setTextFormat(Qt.TextFormat.RichText)
            msgBox.setText(
                f"<b>Imagem promocional de alta resolução (1200x630) gerada com sucesso!</b><br><br>"
                f"Arquivo salvo em:<br><code>{out_path}</code><br><br>"
                f"Perfeita para a <b>Aba Comunidade do YouTube, Discord e Twitter/X</b>."
            )
            btnOpen = msgBox.addButton("📂 Abrir Imagem", QMessageBox.ButtonRole.ActionRole)
            msgBox.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
            msgBox.exec()

            if msgBox.clickedButton() == btnOpen:
                try:
                    os.startfile(out_path)
                except Exception as e:
                    logger.warning(f"Não foi possível abrir a imagem: {e}")
        except Exception as e:
            logger.error(f"Erro ao gerar card social: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro", f"Não foi possível gerar a imagem:\n{e}")

    # -------------------------------------------------------------
    # Web Overlay & 1-Click Playnite Exporter
    # -------------------------------------------------------------
    def onOpenWebOverlay(self):
        url = "http://localhost:8089/overlay"
        try:
            webbrowser.open(url)
        except Exception as e:
            logger.warning(f"Erro ao abrir overlay: {e}")
        
        cb = QApplication.clipboard()
        if cb:
            cb.setText(url)
            QMessageBox.information(
                self,
                "Overlay Web para OBS Studio",
                f"<b>O endereço do overlay foi copiado para sua área de transferência:</b><br><br>"
                f"<code>{url}</code><br><br>"
                f"<b>No OBS Studio:</b><br>"
                f"1. Adicione uma nova fonte do tipo <b>'Navegador' (Browser Source)</b><br>"
                f"2. Cole a URL acima<br>"
                f"3. Defina a largura como <b>600</b> e altura como <b>240</b> (ou 400x320 para o widget de enquete <code>http://localhost:8089/overlay/poll</code>)<br>"
                f"4. Marque 'Controlar áudio via OBS' se desejar."
            )

    def onExportPlaynite(self):
        script_path = os.path.abspath("export_playnite_library.ps1")
        if not os.path.exists(script_path):
            QMessageBox.warning(self, "Aviso", f"Script não encontrado: {script_path}")
            return
        
        progress = QProgressDialog("Disparando exportação da biblioteca do Playnite...", None, 0, 0, self)
        progress.setWindowTitle("Exportando Playnite")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        QApplication.processEvents()

        try:
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            progress.close()

            if res.returncode == 0:
                # Ask to sync sources immediately
                reply = QMessageBox.question(
                    self,
                    "Exportação Concluída",
                    "<b>A biblioteca do Playnite foi exportada com sucesso!</b><br><br>"
                    "Deseja recarregar as fontes e sincronizar os novos jogos no banco de dados agora?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.onSyncSources()
            else:
                QMessageBox.warning(self, "Exportação Playnite", f"A exportação retornou código {res.returncode}:\n{res.stderr[:300]}")
        except Exception as e:
            progress.close()
            logger.error(f"Erro ao rodar export_playnite_library.ps1: {e}")
            QMessageBox.critical(self, "Erro", f"Falha ao executar script de exportação:\n{e}")

    # -------------------------------------------------------------
    # Live History Handlers
    # -------------------------------------------------------------
    def refreshLiveHistoryTable(self):
        records = self.liveHistoryMgr.getLiveHistory(limit=60)
        self.liveTable.setRowCount(len(records))
        for row_idx, r in enumerate(records):
            id_item = QTableWidgetItem(str(r['id']))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.liveTable.setItem(row_idx, 0, id_item)

            date_item = QTableWidgetItem(r['date'])
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.liveTable.setItem(row_idx, 1, date_item)

            game_item = QTableWidgetItem(formatDisplayName(r['gameName']))
            game_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.liveTable.setItem(row_idx, 2, game_item)

            dur_item = QTableWidgetItem(f"{r['duration']}h")
            dur_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.liveTable.setItem(row_idx, 3, dur_item)

            notes_item = QTableWidgetItem(r['notes'] or "—")
            self.liveTable.setItem(row_idx, 4, notes_item)

    def onRecordCurrentHeroLive(self):
        name = formatDisplayName(self.currentChoice)
        self.liveHistoryMgr.recordLive(gameName=self.currentChoice, notes="Sorteado pelo Choose Random Game")
        QMessageBox.information(self, "Live Gravada!", f"O jogo '{name}' foi registrado com sucesso no histórico de transmissões ao vivo!")
        self.refreshLiveHistoryTable()

    def onAddCustomLiveRecord(self):
        notes = self.liveNotesInput.text().strip() or "Transmissão ao vivo no YouTube"
        name = self.currentChoice
        self.liveHistoryMgr.recordLive(gameName=name, notes=notes)
        self.liveNotesInput.clear()
        self.refreshLiveHistoryTable()
        QMessageBox.information(self, "Registrado!", f"Live com '{formatDisplayName(name)}' registrada!")

    def onDeleteSelectedLiveRecord(self):
        row = self.liveTable.currentRow()
        if row >= 0:
            id_item = self.liveTable.item(row, 0)
            if id_item:
                live_id = int(id_item.text())
                self.liveHistoryMgr.deleteLive(live_id)
                self.refreshLiveHistoryTable()

def showDashboard(choosedGame, steamOwnedGames, content, config):
    """Entry point to start the PyQt6 Gaming Dashboard."""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    dashboard = GamingDashboard(content, choosedGame, steamOwnedGames, config)
    dashboard.show()
    app.exec()
