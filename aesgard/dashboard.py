# -*- coding: utf-8 -*-
"""
Modern Gaming Dashboard for Canino Gaming (Inspirado em Caninos Brancos de Jack London).
Refactored modular orchestrator window coordinating UI views, audio, and streaming features.
"""
import os
import sys
import logging
import webbrowser
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSplitter, QMessageBox, QStackedWidget,
    QButtonGroup, QCheckBox, QFrame, QFileDialog, QMenu
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap

from aesgard.ui.styles import STYLESHEET
from aesgard.ui.theme import ThemedCentralWidget, extractChannelHandle, BACKGROUND_PRESETS
from aesgard.ui.views import (
    HeroCardWidget, DatabaseBrowserWidget, GotdView, GotyView,
    ChatChoiceView, LiveHistoryView, SessionBarWidget
)
from aesgard.database import getDatabaseStats, getPlayedGamesSet
from aesgard.gameutil import chooseGame
from aesgard.streamer import LiveHistoryManager, StreamerOverlayWindow
from aesgard.web_overlay import start_overlay_server, update_overlay_channel
from aesgard.sound import get_sound_manager
from aesgard.achievements import AchievementsDialog
from aesgard.analytics import AnalyticsDialog
from aesgard.config_dialog import ConfigDialog
from aesgard.ui import detectPlatform, formatDisplayName

logger = logging.getLogger(__name__)


class GamingDashboard(QMainWindow):
    """
    Main Application Window for Canino Gaming.
    Acts as the lean orchestrator coordinating modular view components:
    - HeroCardWidget (Spotlight randomizer, roulette, mystery mode)
    - DatabaseBrowserWidget (Searchable table and status filters)
    - GotdView (Game of the day - Instinto Selvagem)
    - GotyView (Game of the year - Ouro de Klondike)
    - ChatChoiceView (Triple candidate stream poll)
    - LiveHistoryView (Broadcast logs and notes)
    - SessionBarWidget (Active gameplay stopwatch)
    """

    def __init__(self, content, initialChoice, steamOwnedGames, config):
        super().__init__()
        self.config = config
        self.content = content
        self.currentChoice = initialChoice
        self.steamOwnedGames = steamOwnedGames
        self.currentGotd = None
        self.currentGoty = None
        self.liveHistoryMgr = LiveHistoryManager(dbPath=getattr(self.config, 'DatabaseName', 'Games.db'))
        self.overlayWindow = None

        # Start Web Overlay Server for OBS (port 8089)
        try:
            self.overlayServerStarted = start_overlay_server(port=8089)
            liveChannelUrl = getattr(self.config, 'streamerYouTubeLiveChannel', '').strip()
            mainChannelUrl = getattr(self.config, 'streamerYouTubeMainChannel', '').strip()
            handle = extractChannelHandle(liveChannelUrl or mainChannelUrl, "@Hablocher")
            update_overlay_channel(handle)
        except Exception as e:
            logger.warning(f"Não foi possível iniciar servidor de overlay web: {e}")
            self.overlayServerStarted = False

        self.setWindowTitle("Canino Gaming - Backlog Selvagem & Live Stream Assistant")
        w = getattr(self.config, 'uiWindowWidth', 1280)
        h = getattr(self.config, 'uiWindowHeight', 780)
        min_w = getattr(self.config, 'uiMinWidth', 1100)
        min_h = getattr(self.config, 'uiMinHeight', 680)
        self.resize(w, h)
        self.setMinimumSize(min_w, min_h)
        self.setStyleSheet(STYLESHEET)

        # Central Container with Caninos Brancos Background Theme
        self.bgImagePath = getattr(self.config, 'themeBackgroundImage', 'assets/backgrounds/caninos_brancos_lpm.png')
        self.bgOpacity = getattr(self.config, 'themeBackgroundOpacity', 0.22)
        get_sound_manager().set_theme_mode(getattr(self.config, 'themeSounds', True))

        self.centralContainer = ThemedCentralWidget(self)
        self.setCentralWidget(self.centralContainer)
        self._bgPixmap = None
        if self.bgImagePath and os.path.exists(self.bgImagePath):
            self._bgPixmap = QPixmap(self.bgImagePath)
        self.centralContainer.setBackground(self._bgPixmap, self.bgOpacity)

        self.mainLayout = QVBoxLayout(self.centralContainer)
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        self.mainLayout.setSpacing(14)

        # 1. Header Section (Title, channel links, tools, and Stat Cards)
        self.buildHeaderSection()

        # 2. Navigation Bar (Tabs)
        self.buildNavBar()

        # 2.5 Active Gameplay Session Bar
        self.session_bar = SessionBarWidget(self)
        self.mainLayout.addWidget(self.session_bar)

        # 3. Stacked Container for Views
        self.stack = QStackedWidget()
        self.mainLayout.addWidget(self.stack, 1)

        # View 0: Sorteador Geral & Explorador do Banco
        self.viewMain = self.buildMainView()
        self.stack.addWidget(self.viewMain)

        # View 1: Instinto Selvagem (Game of the Day)
        self.gotd_view = GotdView(self)
        self.stack.addWidget(self.gotd_view)

        # View 2: Hall do GOTY (Ouro de Klondike)
        self.goty_view = GotyView(self)
        self.stack.addWidget(self.goty_view)

        # View 3: Escolha da Matilha (Chat Choice Trio)
        self.chat_choice_view = ChatChoiceView(self)
        self.stack.addWidget(self.chat_choice_view)

        # View 4: Trilhas Percorridas (Live History)
        self.live_history_view = LiveHistoryView(self)
        self.stack.addWidget(self.live_history_view)

        # Initial Data Refresh
        self.updateHeroDisplay(self.currentChoice)
        self.refreshStats()
        self.refreshTable()
        self.gotd_view.onRerollGotd(initial=True)
        self.goty_view.onRerollGoty(initial=True)

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

        # App Title & Subtitle - Canino Gaming (Homenagem a Jack London)
        titleBox = QVBoxLayout()
        titleBox.setSpacing(1)
        titleLabel = QLabel("🐺 CANINO GAMING")
        titleLabel.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titleLabel.setStyleSheet("color: #f0f6fc; letter-spacing: 0.8px;")

        subtitleLabel = QLabel("Caninos Brancos • A Selva do Backlog Gamer & Sorteador Selvagem")
        subtitleLabel.setFont(QFont("Segoe UI", 8))
        subtitleLabel.setStyleSheet("color: #7dd3fc;")

        titleBox.addWidget(titleLabel)
        titleBox.addWidget(subtitleLabel)
        headerLayout.addLayout(titleBox)

        # Web Overlay for OBS Studio
        self.btnWebOverlay = QPushButton("📡 Overlay")
        self.btnWebOverlay.setObjectName("BtnSecondary")
        self.btnWebOverlay.setToolTip("Abre o Overlay HTML5 para OBS Studio no navegador (http://localhost:8089/overlay)")
        self.btnWebOverlay.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnWebOverlay.clicked.connect(self.onOpenWebOverlay)
        headerLayout.addWidget(self.btnWebOverlay)

        # Analytics Button
        self.btnAnalytics = QPushButton("📊 Métricas")
        self.btnAnalytics.setObjectName("BtnSecondary")
        self.btnAnalytics.setToolTip("Abre o painel visual com gráficos de plataformas, taxas de conclusão e horas de backlog")
        self.btnAnalytics.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnAnalytics.clicked.connect(self.onOpenAnalytics)
        headerLayout.addWidget(self.btnAnalytics)

        # Trophies Button
        self.btnAchievements = QPushButton("🏆 Troféus")
        self.btnAchievements.setObjectName("BtnSecondary")
        self.btnAchievements.setToolTip("Galeria com as 12 conquistas e troféus do backlog")
        self.btnAchievements.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnAchievements.clicked.connect(self.onOpenAchievements)
        headerLayout.addWidget(self.btnAchievements)

        # Sound Quick Toggle Button
        self.btnSound = QPushButton("🔊")
        self.btnSound.setFixedWidth(36)
        self.btnSound.setObjectName("BtnSecondary")
        self.btnSound.setToolTip("Silenciar/Ativar efeitos sonoros rapidamente")
        self.btnSound.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnSound.clicked.connect(self.onToggleSound)
        headerLayout.addWidget(self.btnSound)

        # Central Configuration Button
        self.btnConfig = QPushButton("⚙️ Config")
        self.btnConfig.setObjectName("BtnConfig")
        self.btnConfig.setToolTip("Abrir painel completo de configurações (Tema, Fundo, Sons, Streamer, Fontes e Banco)")
        self.btnConfig.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnConfig.clicked.connect(self.onOpenConfigDialog)
        headerLayout.addWidget(self.btnConfig)

        # YouTube Channels
        mainChannelUrl = getattr(self.config, 'streamerYouTubeMainChannel', '').strip()
        liveChannelUrl = getattr(self.config, 'streamerYouTubeLiveChannel', '').strip()

        if mainChannelUrl or liveChannelUrl:
            ytBox = QHBoxLayout()
            ytBox.setSpacing(6)
            if mainChannelUrl:
                mainHandle = extractChannelHandle(mainChannelUrl, "@CanalPrincipal")
                btnYtMain = QPushButton(f"📺 {mainHandle}")
                btnYtMain.setCursor(Qt.CursorShape.PointingHandCursor)
                btnYtMain.setToolTip(f"Canal Principal no YouTube:\n{mainChannelUrl}")
                btnYtMain.setStyleSheet("""
                    QPushButton {
                        background-color: #1a1d26;
                        color: #ff7675;
                        border: 1px solid #ff4757;
                        border-radius: 6px;
                        padding: 4px 8px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #ff4757;
                        color: #ffffff;
                    }
                """)
                btnYtMain.clicked.connect(lambda: webbrowser.open(mainChannelUrl))
                ytBox.addWidget(btnYtMain)

            if liveChannelUrl:
                liveHandle = extractChannelHandle(liveChannelUrl, "@CanalLives")
                btnYtLive = QPushButton(f"🔴 {liveHandle}")
                btnYtLive.setCursor(Qt.CursorShape.PointingHandCursor)
                btnYtLive.setToolTip(f"Canal de Lives no YouTube:\n{liveChannelUrl}")
                btnYtLive.setStyleSheet("""
                    QPushButton {
                        background-color: #1a1d26;
                        color: #a29bfe;
                        border: 1px solid #6c5ce7;
                        border-radius: 6px;
                        padding: 4px 8px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #6c5ce7;
                        color: #ffffff;
                    }
                """)
                btnYtLive.clicked.connect(lambda: webbrowser.open(liveChannelUrl))
                ytBox.addWidget(btnYtLive)

            headerLayout.addLayout(ytBox)

        headerLayout.addStretch()

        # 5 Stat Cards
        self.statTotal = self.createStatCard("0", "TERRITÓRIO")
        self.statInstalled = self.createStatCard("0", "NA TOCA (INSTALADOS)")
        self.statPlayed = self.createStatCard("0", "CAÇADAS (SESSÕES)")
        self.statFinished = self.createStatCard("0", "DOMADOS (ZERADOS)")
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
        layout.setContentsMargins(10, 5, 10, 5)
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

        self.btnNavMain = QPushButton("🐾 Sorteador & Explorador")
        self.btnNavMain.setProperty("class", "NavBtn")
        self.btnNavMain.setCheckable(True)
        self.btnNavMain.setChecked(True)
        self.btnNavMain.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnNavMain.clicked.connect(lambda: self.switchView(0))

        self.btnNavGotd = QPushButton("❄️ Instinto Selvagem (Jogo do Dia)")
        self.btnNavGotd.setProperty("class", "NavBtn")
        self.btnNavGotd.setCheckable(True)
        self.btnNavGotd.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnNavGotd.clicked.connect(lambda: self.switchView(1))

        self.btnNavGoty = QPushButton("🏆 Hall do GOTY (Ouro de Klondike)")
        self.btnNavGoty.setProperty("class", "NavBtn")
        self.btnNavGoty.setCheckable(True)
        self.btnNavGoty.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnNavGoty.clicked.connect(lambda: self.switchView(2))

        self.btnNavChatChoice = QPushButton("🐺 Escolha da Matilha (Chat)")
        self.btnNavChatChoice.setProperty("class", "NavBtn")
        self.btnNavChatChoice.setCheckable(True)
        self.btnNavChatChoice.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnNavChatChoice.clicked.connect(lambda: self.switchView(3))

        self.btnNavLiveHistory = QPushButton("📜 Trilhas Percorridas (Lives)")
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
        self.chkRoulette.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")
        navLayout.addWidget(self.chkRoulette)

        self.btnObsOverlay = QPushButton("🎥 Overlay OBS")
        self.btnObsOverlay.setObjectName("BtnSecondary")
        self.btnObsOverlay.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnObsOverlay.setToolTip("Abre uma janela limpa com capa e título para captura direta de janela no OBS Studio")
        self.btnObsOverlay.clicked.connect(self.onOpenObsOverlay)
        navLayout.addWidget(self.btnObsOverlay)

        self.mainLayout.addLayout(navLayout)

    def switchView(self, index):
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.btnNavMain.setChecked(True)
        elif index == 1:
            self.btnNavGotd.setChecked(True)
        elif index == 2:
            self.btnNavGoty.setChecked(True)
            self.goty_view.refreshGotyTable()
        elif index == 3:
            self.btnNavChatChoice.setChecked(True)
            if not self.chat_choice_view.chatChoiceTrio:
                self.chat_choice_view.onRerollChatChoice()
        elif index == 4:
            self.btnNavLiveHistory.setChecked(True)
            self.live_history_view.refreshLiveHistoryTable()

    # -------------------------------------------------------------
    # 3. View 0: Sorteador Geral & Explorador do Banco
    # -------------------------------------------------------------
    def buildMainView(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Quick Live Themes Bar - Yukon Instincts
        themeRow = QHBoxLayout()
        themeRow.setSpacing(8)
        themeLbl = QLabel("🐺 INSTINTO & TEMA:")
        themeLbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        themeLbl.setStyleSheet("color: #38bdf8; letter-spacing: 1px;")
        themeRow.addWidget(themeLbl)

        themes = [
            ("❄️ Todo o Território", "all"),
            ("🐺 Presas Intocadas (0x)", "backlog"),
            ("🎮 Consoles & Emuladores", "emulators"),
            ("🕹️ Só Retrô (eXoDOS)", "retro"),
            ("🚀 Só PC / Lojas", "modern"),
            ("⭐ Favoritos da Matilha", "favorites")
        ]
        for t_label, t_mode in themes:
            btn = QPushButton(t_label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #0c1522;
                    border: 1px solid #1c2f44;
                    border-radius: 6px;
                    padding: 5px 12px;
                    font-size: 11px;
                    font-weight: bold;
                    color: #c8daea;
                }
                QPushButton:hover {
                    background-color: #152438;
                    border-color: #38bdf8;
                    color: #ffffff;
                }
            """)
            btn.clicked.connect(lambda _, m=t_mode: self.onApplyLiveTheme(m))
            themeRow.addWidget(btn)

        themeRow.addStretch()
        layout.addLayout(themeRow)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)

        # Modular Hero Card Widget
        self.hero_card = HeroCardWidget(self)
        splitter.addWidget(self.hero_card)

        # Modular Database Browser Widget
        self.database_browser = DatabaseBrowserWidget(self)
        splitter.addWidget(self.database_browser)

        splitter.setSizes([460, 680])
        layout.addWidget(splitter)
        return widget

    def onApplyLiveTheme(self, mode):
        if not hasattr(self, 'hero_card'):
            return
        combo = getattr(self.hero_card, 'comboRerollFilter', None)
        if mode == "all" and combo:
            combo.setCurrentIndex(0)
        elif mode == "emulators" and combo:
            idx = combo.findText("Emuladores", Qt.MatchFlag.MatchContains)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        elif mode == "retro" and combo:
            idx = combo.findText("eXoDOS", Qt.MatchFlag.MatchContains)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        elif mode == "modern" and combo:
            idx = combo.findText("Playnite", Qt.MatchFlag.MatchContains)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        elif mode == "favorites" and combo:
            idx = combo.findText("Favoritos", Qt.MatchFlag.MatchContains)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            else:
                self.hero_card.onRerollHero()
            return
        elif mode == "backlog":
            played_names = getPlayedGamesSet()
            zeros = [g for g in self.content if g not in played_names]
            if zeros:
                sample_size = getattr(self.config, 'randomSampleSize', 25)
                new_choice = chooseGame(zeros, sampleSize=sample_size)
                if self.chkRoulette.isChecked():
                    self.hero_card.startRouletteAnimation(lambda: self.updateHeroDisplay(new_choice))
                else:
                    self.updateHeroDisplay(new_choice)
            else:
                QMessageBox.information(self, "Tema da Live", "Parabéns! Todos os jogos já foram jogados pelo menos uma vez.")
            return

        self.hero_card.onRerollHero()

    # -------------------------------------------------------------
    # State Coordination & Delegate Methods
    # -------------------------------------------------------------
    def updateHeroDisplay(self, gameEntry):
        self.currentChoice = gameEntry
        if hasattr(self, 'hero_card'):
            self.hero_card.updateHeroDisplay(gameEntry)

    def refreshStats(self):
        stats = getDatabaseStats()
        total = stats.get("total", len(self.content))
        installed = stats.get("installed", 0)
        played = stats.get("played", 0)
        finished = stats.get("finished", 0)

        pct = round((finished / total) * 100, 1) if total > 0 else 0

        self.statTotal.findChild(QLabel, "StatValue").setText(str(total))
        self.statInstalled.findChild(QLabel, "StatValue").setText(str(installed))
        self.statPlayed.findChild(QLabel, "StatValue").setText(str(played))
        self.statFinished.findChild(QLabel, "StatValue").setText(str(finished))
        self.statBacklog.findChild(QLabel, "StatValue").setText(f"{pct}%")

    def refreshTable(self):
        if hasattr(self, 'database_browser'):
            self.database_browser.refreshTable()

    def refreshGotyTable(self):
        if hasattr(self, 'goty_view'):
            self.goty_view.refreshGotyTable()

    def refreshLiveHistoryTable(self):
        if hasattr(self, 'live_history_view'):
            self.live_history_view.refreshLiveHistoryTable()

    def onRerollGotd(self, initial=False):
        if hasattr(self, 'gotd_view'):
            self.gotd_view.onRerollGotd(initial=initial)

    def onRerollGoty(self, initial=False):
        if hasattr(self, 'goty_view'):
            self.goty_view.onRerollGoty(initial=initial)

    def onRerollChatChoice(self):
        if hasattr(self, 'chat_choice_view'):
            self.chat_choice_view.onRerollChatChoice()

    def startGameplaySession(self, gameEntry):
        if hasattr(self, 'session_bar'):
            self.session_bar.startGameplaySession(gameEntry)

    def onStopGameplaySession(self):
        if hasattr(self, 'session_bar'):
            self.session_bar.onStopGameplaySession()

    # -------------------------------------------------------------
    # Dialogs & Global Actions
    # -------------------------------------------------------------
    def onOpenConfigDialog(self):
        get_sound_manager().play("click")
        dlg = ConfigDialog(self, self.config)
        dlg.themeChanged.connect(self._on_theme_changed)
        dlg.exec()

    def _on_theme_changed(self, bg_path: str, opacity: float, theme_sounds: bool):
        self.setBackgroundPreset(bg_path, opacity)
        get_sound_manager().set_theme_mode(theme_sounds)

    def onOpenWebOverlay(self):
        get_sound_manager().play("click")
        webbrowser.open("http://localhost:8089/overlay")

    def onOpenAnalytics(self):
        get_sound_manager().play("click")
        dlg = AnalyticsDialog(self.content, self)
        dlg.exec()

    def onOpenAchievements(self):
        get_sound_manager().play("click")
        dlg = AchievementsDialog(self)
        dlg.exec()

    def onToggleSound(self):
        sm = get_sound_manager()
        new_state = not sm.is_muted()
        sm.set_mute(new_state)
        self.btnSound.setText("🔇" if new_state else "🔊")
        if not new_state:
            sm.play("click")

    def onOpenObsOverlay(self):
        if not self.overlayWindow or not self.overlayWindow.isVisible():
            pix = getattr(self.hero_card, 'imageLabel', None)
            cover_pixmap = pix.pixmap() if pix else None
            platform = detectPlatform(self.currentChoice)
            self.overlayWindow = StreamerOverlayWindow(
                gameTitle=formatDisplayName(self.currentChoice),
                coverPixmap=cover_pixmap,
                platformText=platform
            )
            self.overlayWindow.show()
        else:
            self.overlayWindow.activateWindow()

    def setBackgroundPreset(self, path: str, opacity: float = None):
        """Applies a background image preset and persists settings to choose_random_game.ini."""
        if opacity is not None:
            self.bgOpacity = opacity
        self.bgImagePath = path or ""
        if self.bgImagePath and os.path.exists(self.bgImagePath):
            self._bgPixmap = QPixmap(self.bgImagePath)
        else:
            self._bgPixmap = None

        if hasattr(self, 'centralContainer'):
            self.centralContainer.setBackground(self._bgPixmap, self.bgOpacity)

        if hasattr(self.config, 'save_theme_setting'):
            self.config.save_theme_setting(self.bgImagePath, self.bgOpacity)
        get_sound_manager().play("snow_crunch")


def showDashboard(choosedGame, steamOwnedGames, content, config):
    """Entry point to start the PyQt6 Gaming Dashboard."""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    dashboard = GamingDashboard(content, choosedGame, steamOwnedGames, config)
    dashboard.show()
    app.exec()
