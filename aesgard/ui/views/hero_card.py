# -*- coding: utf-8 -*-
"""
Hero Card (Presa Sorteada) Component for Canino Gaming.
The primary spotlight picker featuring random selection, roulette animation,
HowLongToBeat metadata badge, mystery box mode, challenges, and stream suite actions.
"""
import random
import threading
import logging
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QMessageBox,
    QInputDialog
)
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QFont, QPixmap, QImage, QColor, QPainter, QPen

from aesgard.gameutil import (
    executeGame, installGame, findGameIcon, chooseGame,
    linkPrefix, exodosPrefix
)
from aesgard.playnite import PLAYNITE_PREFIX
from aesgard.database import (
    findGameInfo, setFavorite, setFinished, getDatabaseStats,
    getInstalledGamesSet, getUninstalledGamesSet, getFavoriteGamesSet, getPlayedGamesSet
)
from aesgard.ui import formatDisplayName, detectPlatform, getPlatformColor, extractChannelHandle
from aesgard.intel_dialog import GameIntelDialog
from aesgard.hltb import (
    get_cached_hltb, fetch_hltb_data, format_hltb_duration, get_duration_badge_style,
    clean_title_for_hltb, get_all_cached_durations, preload_hltb_cache
)
from aesgard.web_overlay import update_overlay_game
from aesgard.wheel_dialog import WheelOfFortuneDialog
from aesgard.card_generator import generate_live_card
from aesgard.sound import get_sound_manager
from aesgard.vibe import filter_games_by_vibe, generate_curator_pitch
from aesgard.challenges import get_random_challenge, set_active_challenge, clear_challenge
from aesgard.bingo import LiveBingoDialog
from aesgard.chat_bot import get_chat_bot
from aesgard.achievements import unlock_achievement
from aesgard.backup import backup_game_saves

logger = logging.getLogger(__name__)


class HeroCardWidget(QFrame):
    """Component for the primary random game spotlight card and associated actions."""
    def __init__(self, dashboard, parent=None):
        super().__init__(parent)
        self.dashboard = dashboard
        self.isMysteryMode = False
        self.mysteryRevealed = False
        self._rouletteTimer = None
        self._rouletteTicks = 0
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("HeroCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Section Header
        heroHeader = QHBoxLayout()
        headerText = QLabel("🐺 PRESA SORTEADA")
        headerText.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        headerText.setStyleSheet("color: #38bdf8; letter-spacing: 1px;")

        self.installBadge = QLabel("✔ INSTALADO")
        self.installBadge.setObjectName("InstallBadge")
        self.installBadge.setStyleSheet(
            "background-color: #059669; color: #ffffff; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;"
        )

        self.platformBadge = QLabel("LOCAL")
        self.platformBadge.setObjectName("PlatformBadge")

        self.hltbBadge = QLabel("⏱️ HLTB: --")
        self.hltbBadge.setObjectName("HltbBadge")
        self.hltbBadge.setStyleSheet(
            "background-color: #0284c7; color: #ffffff; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;"
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
        cfg = getattr(self.dashboard, 'config', None)
        cover_w = getattr(cfg, 'uiCoverWidth', 160) if cfg else 160
        cover_h = getattr(cfg, 'uiCoverHeight', 160) if cfg else 160
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

        # Challenge Banner (dismissible)
        self.challengeBanner = QFrame()
        self.challengeBanner.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #450a0a, stop:1 #1e1b4b);
                border: 2px solid #ef4444;
                border-radius: 8px;
                padding: 6px 10px;
            }
        """)
        ch_l = QHBoxLayout(self.challengeBanner)
        ch_l.setContentsMargins(6, 4, 6, 4)
        ch_l.setSpacing(8)
        self.challengeIconLbl = QLabel("💀")
        self.challengeIconLbl.setFont(QFont("Segoe UI", 16))
        ch_l.addWidget(self.challengeIconLbl)
        self.challengeTitleLbl = QLabel("Desafio da Live Ativo")
        self.challengeTitleLbl.setStyleSheet("color: #fca5a5; font-size: 11px;")
        self.challengeTitleLbl.setWordWrap(True)
        ch_l.addWidget(self.challengeTitleLbl, 1)

        btnDismissCh = QPushButton("✕")
        btnDismissCh.setFixedSize(22, 22)
        btnDismissCh.setStyleSheet("QPushButton { background: transparent; color: #f87171; font-weight: bold; border: none; } QPushButton:hover { color: #ffffff; }")
        btnDismissCh.clicked.connect(lambda: (clear_challenge(), self.challengeBanner.hide()))
        ch_l.addWidget(btnDismissCh)
        self.challengeBanner.hide()
        layout.addWidget(self.challengeBanner)

        # Big Play Button - Caçar
        self.btnPlay = QPushButton("▶  CAÇAR AGORA (JOGAR)")
        self.btnPlay.setObjectName("BtnPlay")
        self.btnPlay.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnPlay.clicked.connect(self.onPlayHero)
        layout.addWidget(self.btnPlay)

        # Reroll Button - Nova Presa
        self.btnReroll = QPushButton("🎲  SORTEAR NOVA PRESA (REROLL)")
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

        self.btnCuratorPitch = QPushButton("💡 Por que Jogar?")
        self.btnCuratorPitch.setObjectName("BtnSecondary")
        self.btnCuratorPitch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnCuratorPitch.setToolTip("Exibe a resenha rápida de curadoria e dicas para manter o chat engajado")
        self.btnCuratorPitch.clicked.connect(self.onOpenCuratorPitch)

        self.btnRecordHeroLive = QPushButton("🔴 Gravar na Live")
        self.btnRecordHeroLive.setObjectName("BtnSecondary")
        self.btnRecordHeroLive.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnRecordHeroLive.setToolTip("Registra este jogo no histórico de transmissões ao vivo do seu canal")
        self.btnRecordHeroLive.clicked.connect(self.onRecordCurrentHeroLive)

        intelRow.addWidget(self.btnHeroIntel)
        intelRow.addWidget(self.btnCuratorPitch)
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

        # Live Tools Row (Row 3: Desafio, Bingo, Backup, Bot Twitch)
        toolsRow = QHBoxLayout()
        toolsRow.setSpacing(6)

        self.btnLiveChallenge = QPushButton("💀 Desafio Live")
        self.btnLiveChallenge.setObjectName("BtnSecondary")
        self.btnLiveChallenge.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnLiveChallenge.setToolTip("Sorteia um desafio ou penalidade cômica para o streamer cumprir ao vivo")
        self.btnLiveChallenge.clicked.connect(self.onRollLiveChallenge)
        toolsRow.addWidget(self.btnLiveChallenge)

        self.btnLiveBingo = QPushButton("🎯 Bingo")
        self.btnLiveBingo.setObjectName("BtnSecondary")
        self.btnLiveBingo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnLiveBingo.setToolTip("Abre a cartela interativa de Bingo da Live (também visível no OBS em /bingo)")
        self.btnLiveBingo.clicked.connect(self.onOpenLiveBingo)
        toolsRow.addWidget(self.btnLiveBingo)

        self.btnBackupSave = QPushButton("💾 Backup Save")
        self.btnBackupSave.setObjectName("BtnSecondary")
        self.btnBackupSave.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnBackupSave.setToolTip("Cria um backup compactado .zip instantâneo dos saves deste jogo")
        self.btnBackupSave.clicked.connect(self.onBackupCurrentSave)
        toolsRow.addWidget(self.btnBackupSave)

        self.btnChatBot = QPushButton("💬 Bot Twitch")
        self.btnChatBot.setObjectName("BtnSecondary")
        self.btnChatBot.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnChatBot.setToolTip("Conecta ao chat da Twitch para receber votos !voto 1/2/3 automaticamente")
        self.btnChatBot.clicked.connect(self.onToggleChatBot)
        toolsRow.addWidget(self.btnChatBot)

        layout.addLayout(toolsRow)

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
            "⏱️ Jogos Longos (> 25h HLTB)",
            "🧘 Vibe: Zen & Relaxar",
            "⚡ Vibe: Pura Adrenalina",
            "👻 Vibe: Terror & Suspense",
            "📜 Vibe: História & Imersão",
            "🕹️ Vibe: Nostalgia Retrô",
            "🧠 Vibe: Estratégia & Raciocínio"
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

    def updateHeroDisplay(self, gameEntry):
        if not gameEntry:
            return
        self.dashboard.currentChoice = gameEntry
        display_name = formatDisplayName(gameEntry)
        platform = detectPlatform(gameEntry)

        if self.isMysteryMode and not self.mysteryRevealed:
            self.gameTitleLabel.setText("🕵️ JOGO MISTERIOSO\n(Clique aqui ou na capa para revelar!)")
            self.gameTitleLabel.setCursor(Qt.CursorShape.PointingHandCursor)
            self.platformBadge.setText("MISTERIOSO")
            self.platformBadge.setStyleSheet("background-color: #6366f1; color: #ffffff; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;")
            self.hltbBadge.setText("⏱️ ??h (HLTB)")
            self.hltbBadge.setStyleSheet("background-color: #475569; color: #cbd5e1; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;")
            self.gameStatsLabel.setText("Modo suspense ativado! Capa e título ocultos para o chat.")

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

            self.btnMysteryMode.setChecked(True)
            self.btnMysteryMode.setText("👁️ Revelar Jogo")
            update_overlay_game("❓ Jogo Misterioso", "???", "??h")
            return

        self.gameTitleLabel.setText(display_name)
        self.gameTitleLabel.setCursor(Qt.CursorShape.ArrowCursor)
        self.imageLabel.setCursor(Qt.CursorShape.ArrowCursor)
        self.imageLabel.mousePressEvent = None
        self.gameTitleLabel.mousePressEvent = None

        self.btnMysteryMode.setChecked(False)
        self.btnMysteryMode.setText("🕵️ Misterioso")

        self.platformBadge.setText(platform.upper())
        self.platformBadge.setStyleSheet(
            f"background-color: {getPlatformColor(platform)}; color: #ffffff; "
            f"border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;"
        )

        overlay_hltb = "--"
        def _apply_hltb_ui(data):
            if data:
                hours = data.get("main_story", 0.0) or data.get("main_extra", 0.0) or data.get("completionist", 0.0)
                if hours and hours > 0:
                    dur_str = format_hltb_duration(hours)
                    self.hltbBadge.setText(dur_str)
                    self.hltbBadge.setStyleSheet(get_duration_badge_style(hours))
                    self.hltbBadge.setToolTip(
                        f"Campanha Principal: {data.get('main_story', 0):.1f}h\n"
                        f"História + Extras: {data.get('main_extra', 0):.1f}h\n"
                        f"Complecionista (100%): {data.get('completionist', 0):.1f}h"
                    )
                    update_overlay_game(display_name, platform, f"~{hours:.1f}h")
                    return
            self.hltbBadge.setText("⏱️ HLTB: --")
            self.hltbBadge.setStyleSheet("background-color: #334155; color: #94a3b8; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;")
            self.hltbBadge.setToolTip("Tempo não catalogado no HowLongToBeat")
            update_overlay_game(display_name, platform, "--")

        try:
            hltb_info = get_cached_hltb(display_name)
            if hltb_info is not None:
                _apply_hltb_ui(hltb_info)
                hours = hltb_info.get('main_story', 0) or hltb_info.get('main_extra', 0) or hltb_info.get('completionist', 0)
                if hours > 0:
                    overlay_hltb = f"~{hours:.1f}h"
            else:
                self.hltbBadge.setText("⏱️ HLTB: ...")
                self.hltbBadge.setStyleSheet("background-color: #1e293b; color: #38bdf8; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;")
                self.hltbBadge.setToolTip("Consultando estimativa no HowLongToBeat em segundo plano...")
                overlay_hltb = "--"

                def _fetch_bg(target_entry, target_name):
                    res = None
                    try:
                        res = fetch_hltb_data(target_name, timeout=5.0)
                    except Exception as ex:
                        logger.debug(f"Async HLTB error: {ex}")
                        res = None
                    finally:
                        def _update_if_current():
                            if getattr(self.dashboard, 'currentChoice', None) == target_entry:
                                _apply_hltb_ui(res)
                        QTimer.singleShot(0, _update_if_current)

                threading.Thread(target=_fetch_bg, args=(gameEntry, display_name), daemon=True).start()
        except Exception as e:
            logger.debug(f"Erro ao obter badge HLTB: {e}")
            _apply_hltb_ui(None)
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

        if is_installed:
            self.installBadge.setText("✔ INSTALADO")
            self.installBadge.setStyleSheet(
                "background-color: #00b894; color: #ffffff; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;"
            )
            self.btnPlay.setText("▶  CAÇAR AGORA (JOGAR)")
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
            self.installBadge.setText("⏳ NÃO INSTALADO")
            self.installBadge.setStyleSheet(
                "background-color: #6c5ce7; color: #ffffff; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;"
            )
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

        try:
            cfg = getattr(self.dashboard, 'config', None)
            pn_path = getattr(cfg, 'playnitePath', '') if cfg else ''
            pilImg = findGameIcon(gameEntry, playnitePath=pn_path)
            pilImg = pilImg.convert("RGBA")
            data = pilImg.tobytes("raw", "RGBA")
            qim = QImage(data, pilImg.size[0], pilImg.size[1], QImage.Format.Format_RGBA8888)
            cover_w = getattr(cfg, 'uiCoverWidth', 160) if cfg else 160
            cover_h = getattr(cfg, 'uiCoverHeight', 160) if cfg else 160
            pix = QPixmap.fromImage(qim).scaled(cover_w, cover_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.imageLabel.setPixmap(pix)
            if hasattr(self.dashboard, 'overlayWindow') and self.dashboard.overlayWindow and self.dashboard.overlayWindow.isVisible():
                self.dashboard.overlayWindow.updateGame(display_name, pix, platform)
            update_overlay_game(display_name, platform, overlay_hltb)
        except Exception as e:
            logger.warning(f"Error rendering icon in dashboard: {e}")

    def onPlayHero(self):
        target = getattr(self.dashboard, 'currentChoice', None)
        if not target:
            return
        info = findGameInfo(target)
        is_installed = (info[6] == 1) if (info and len(info) >= 7) else 1

        if is_installed:
            logger.info(f"Launching game from Hero Card: {target}")
            if hasattr(self.dashboard, 'startGameplaySession'):
                self.dashboard.startGameplaySession(target)
            self.dashboard.showMinimized()
            executeGame(target, getattr(self.dashboard, 'steamOwnedGames', []))
        else:
            logger.info(f"Installing uninstalled game: {target}")
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

        if hasattr(self.dashboard, 'refreshStats'):
            self.dashboard.refreshStats()
        if hasattr(self.dashboard, 'refreshTable'):
            self.dashboard.refreshTable()
        self.updateHeroDisplay(target)

    def onRerollHero(self):
        filter_mode = self.comboRerollFilter.currentText()
        content = getattr(self.dashboard, 'content', [])
        filtered_content = content

        if "Apenas Instalados" in filter_mode:
            inst_names = getInstalledGamesSet()
            filtered_content = [g for g in content if g in inst_names] or list(inst_names)
        elif "Apenas Não Instalados" in filter_mode:
            uninst_names = getUninstalledGamesSet()
            filtered_content = [g for g in content if g in uninst_names] or list(uninst_names)
        elif "Favoritos" in filter_mode:
            fav_names = getFavoriteGamesSet()
            filtered_content = [g for g in content if g in fav_names] or list(fav_names)
        elif "eXoDOS" in filter_mode:
            filtered_content = [g for g in content if g.startswith(exodosPrefix) or "exodos" in g.lower()]
        elif "Atalhos" in filter_mode:
            filtered_content = [g for g in content if g.startswith(linkPrefix)]
        elif "Locais" in filter_mode:
            filtered_content = [g for g in content if not g.startswith(linkPrefix) and not g.startswith(exodosPrefix) and not g.startswith(PLAYNITE_PREFIX)]
        elif "Curtos" in filter_mode:
            preload_hltb_cache()
            all_durations = get_all_cached_durations()
            short_cands = [g for g in content if 0 < all_durations.get(clean_title_for_hltb(formatDisplayName(g)).lower(), 0.0) < 5.0]
            filtered_content = short_cands if len(short_cands) >= 5 else content
        elif "Vibe: " in filter_mode:
            v_map = {"Zen": "zen", "Adrenalina": "adrenaline", "Terror": "horror", "História": "story", "Retrô": "retro", "Estratégia": "strategy"}
            v_k = next((val for k, val in v_map.items() if k in filter_mode), "zen")
            filtered_content = filter_games_by_vibe(content, v_k)

        if not filtered_content:
            filtered_content = content

        def do_pick():
            cfg = getattr(self.dashboard, 'config', None)
            s_size = getattr(cfg, 'randomSampleSize', 25) if cfg else 25
            new_choice = chooseGame(filtered_content, sampleSize=s_size)
            self.updateHeroDisplay(new_choice)

        chk_roulette = getattr(self.dashboard, 'chkRoulette', None)
        if chk_roulette and chk_roulette.isChecked():
            self.startRouletteAnimation(do_pick)
        else:
            get_sound_manager().play("reveal")
            do_pick()

    def startRouletteAnimation(self, on_finished_callback):
        if hasattr(self, '_rouletteTimer') and self._rouletteTimer and self._rouletteTimer.isActive():
            return

        get_sound_manager().play("blizzard_wind")
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
        if self._rouletteTicks % 2 == 0:
            get_sound_manager().play("snow_crunch")
        else:
            get_sound_manager().play("tick")

        content = getattr(self.dashboard, 'content', [])
        if content:
            cand = random.choice(content)
            self.gameTitleLabel.setText(f"🎲 {formatDisplayName(cand)}...")
            self.platformBadge.setText("SORTEANDO...")
            self.platformBadge.setStyleSheet("background-color: #6c5ce7; color: #ffffff; border-radius: 6px; padding: 3px 8px; font-weight: bold;")

        if self._rouletteTicks > 8:
            self._rouletteInterval = int(self._rouletteInterval * 1.25)
            self._rouletteTimer.setInterval(self._rouletteInterval)

        if self._rouletteTicks >= self._rouletteTotalTicks:
            self._rouletteTimer.stop()
            self.btnReroll.setEnabled(True)
            get_sound_manager().play("reveal")
            if self._rouletteCallback:
                self._rouletteCallback()

    def onToggleFavorite(self):
        choice = getattr(self.dashboard, 'currentChoice', None)
        if not choice:
            return
        info = findGameInfo(choice)
        current_fav = info[5] if info else 0
        new_fav = 0 if current_fav else 1
        setFavorite(choice, new_fav)
        self.updateHeroDisplay(choice)
        if hasattr(self.dashboard, 'refreshStats'):
            self.dashboard.refreshStats()
        if hasattr(self.dashboard, 'refreshTable'):
            self.dashboard.refreshTable()

    def onToggleFinished(self):
        choice = getattr(self.dashboard, 'currentChoice', None)
        if not choice:
            return
        info = findGameInfo(choice)
        current_fin = info[4] if info else 0
        new_fin = 0 if current_fin else 1
        setFinished(choice, new_fin)
        if new_fin == 1:
            get_sound_manager().play("victory")
            unlock_achievement("first_blood", self)
            stats = getDatabaseStats()
            if stats.get("finished", 0) >= 5:
                unlock_achievement("backlog_warrior", self)
            if stats.get("finished", 0) >= 10:
                unlock_achievement("backlog_master", self)
        self.updateHeroDisplay(choice)
        if hasattr(self.dashboard, 'refreshStats'):
            self.dashboard.refreshStats()
        if hasattr(self.dashboard, 'refreshTable'):
            self.dashboard.refreshTable()

    def onToggleMysteryMode(self):
        self.isMysteryMode = not self.isMysteryMode
        self.mysteryRevealed = False
        self.updateHeroDisplay(getattr(self.dashboard, 'currentChoice', None))

    def onRevealMysteryGame(self):
        if self.isMysteryMode and not self.mysteryRevealed:
            self.mysteryRevealed = True
            get_sound_manager().play("reveal")
            unlock_achievement("mystery_solver", self)
            self.updateHeroDisplay(getattr(self.dashboard, 'currentChoice', None))

    def onOpenHeroIntel(self):
        choice = getattr(self.dashboard, 'currentChoice', None)
        if not choice:
            return
        pix = self.imageLabel.pixmap()
        dlg = GameIntelDialog(choice, coverPixmap=pix, parent=self)
        dlg.exec()

    def onOpenCuratorPitch(self):
        choice = getattr(self.dashboard, 'currentChoice', None)
        if not choice:
            return
        get_sound_manager().play("click")
        pitch = generate_curator_pitch(choice)
        msg = QMessageBox(self)
        msg.setWindowTitle(f"💡 Por que Jogar Hoje? - {pitch['title']}")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(f"""
        <div style='font-family: Segoe UI, sans-serif;'>
            <h2 style='color: #38bdf8; margin-bottom: 4px;'>{pitch['vibe_emoji']} {pitch['title']}</h2>
            <p style='color: {pitch['vibe_color']}; font-weight: bold; font-size: 12px;'>
                {pitch['vibe_name'].upper()} • {pitch['duration']}
            </p>
            <p style='font-size: 13px; color: #ffffff; margin-top: 10px;'>
                <b>🎯 Por que vale a pena:</b><br>{pitch['hook']}
            </p>
            <p style='font-size: 12px; color: #cbd5e1; margin-top: 10px;'>
                <i>{pitch['vibe_desc']}</i>
            </p>
            <div style='background-color: #1e293b; border-left: 3px solid #f59e0b; padding: 8px 12px; border-radius: 6px; margin-top: 12px;'>
                <p style='color: #fbbf24; font-size: 12px; margin: 0;'>
                    {pitch['streamer_tip']}
                </p>
            </div>
        </div>
        """)
        msg.exec()

    def onRecordCurrentHeroLive(self):
        if hasattr(self.dashboard, 'liveHistoryView'):
            self.dashboard.liveHistoryView.onRecordCurrentHeroLive()

    def onOpenWheelOfFortune(self):
        pool = getattr(self.dashboard, 'content', [])
        cands_count = min(12, len(pool))
        cands = random.sample(pool, cands_count) if len(pool) >= cands_count else pool
        dlg = WheelOfFortuneDialog(cands, self)
        if dlg.exec():
            winner = dlg.get_winner()
            if winner:
                self.updateHeroDisplay(winner)
                if hasattr(self.dashboard, 'stack'):
                    self.dashboard.stack.setCurrentIndex(0)
                if hasattr(self.dashboard, 'btnNavMain'):
                    self.dashboard.btnNavMain.setChecked(True)

    def onGenerateSocialCard(self):
        choice = getattr(self.dashboard, 'currentChoice', None)
        if not choice:
            return
        pix = self.imageLabel.pixmap()
        cfg = getattr(self.dashboard, 'config', None)
        main_url = getattr(cfg, 'streamerYouTubeMainChannel', '') if cfg else ''
        try:
            from aesgard.ui.theme import extractChannelHandle
            handle = extractChannelHandle(main_url, "@CaninoGaming")
            out_path = generate_live_card(choice, cover_pixmap=pix, channel_name=handle)
            if out_path:
                QMessageBox.information(self, "Card da Live Gerado", f"Card salvo com sucesso em:\n{out_path}")
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"Não foi possível gerar o card social: {e}")

    def onRollLiveChallenge(self):
        ch = get_random_challenge()
        set_active_challenge(ch)
        get_sound_manager().play("reveal")
        unlock_achievement("challenger", self)
        self.challengeBanner.show()
        self.challengeIconLbl.setText(ch["icon"])
        self.challengeTitleLbl.setText(f"<b>{ch['title']}</b> ({ch['category']}): {ch['desc']}")

    def onOpenLiveBingo(self):
        dlg = LiveBingoDialog(parent=self)
        dlg.exec()

    def onBackupCurrentSave(self):
        choice = getattr(self.dashboard, 'currentChoice', None)
        res = backup_game_saves(game_name=choice)
        if res.get("success"):
            QMessageBox.information(self, "Backup Criado!", f"Backup criado em:\n{res.get('archive_path')}")
        else:
            QMessageBox.warning(self, "Falha no Backup", f"Erro: {res.get('error')}")

    def onToggleChatBot(self):
        bot = get_chat_bot()
        if bot.is_connected():
            bot.stop_bot()
            self.btnChatBot.setText("💬 Bot Twitch")
            self.btnChatBot.setStyleSheet("")
            QMessageBox.information(self, "Bot Desconectado", "Bot da Twitch desconectado com sucesso.")
            return

        def_channel = ""
        cfg = getattr(self.dashboard, 'config', None)
        if cfg:
            def_channel = getattr(cfg, 'streamerTwitchChannel', '') or ''
            if not def_channel:
                yt_url = getattr(cfg, 'streamerYouTubeMainChannel', '') or getattr(cfg, 'streamerYouTubeLiveChannel', '')
                def_channel = extractChannelHandle(yt_url).lstrip("@")

        channel, ok = QInputDialog.getText(
            self,
            "Conectar Bot da Twitch (Leitura de Votos)",
            "Digite o canal da Twitch para computar votos automaticamente (!voto 1, !voto 2, !voto 3):\n(Não necessita de senha ou token para votar)",
            text=def_channel
        )
        if not ok or not channel.strip():
            return

        clean_channel = channel.strip().lstrip("#").lower()

        try:
            bot.vote_received.disconnect(self._on_bot_vote_received)
        except Exception:
            pass
        try:
            bot.status_changed.disconnect(self._on_bot_status_changed)
        except Exception:
            pass

        bot.vote_received.connect(self._on_bot_vote_received)
        bot.status_changed.connect(self._on_bot_status_changed)

        bot.start_bot(clean_channel)
        self.btnChatBot.setText(f"🟢 #{clean_channel[:10]}")
        self.btnChatBot.setStyleSheet("""
            QPushButton {
                background-color: #065f46;
                border: 1px solid #10b981;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
                color: #ffffff;
            }
        """)

    def _on_bot_vote_received(self, option_idx: int, username: str):
        choice_view = getattr(self.dashboard, 'chat_choice_view', None) or getattr(self.dashboard, 'chatChoiceView', None)
        if choice_view and hasattr(choice_view, 'onAddChatVote'):
            choice_view.onAddChatVote(option_idx)
        get_sound_manager().play("click")
        unlock_achievement("democracy", self.dashboard or self)

    def _on_bot_status_changed(self, connected: bool, msg: str):
        if not connected and hasattr(self, 'btnChatBot'):
            self.btnChatBot.setText("💬 Bot Twitch")
            self.btnChatBot.setStyleSheet("")
