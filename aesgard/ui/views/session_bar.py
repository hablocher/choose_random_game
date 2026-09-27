# -*- coding: utf-8 -*-
"""
Live Gameplay Session Bar & Stopwatch Component for Canino Gaming.
Tracks real-time session duration and synchronizes with OBS Web Overlay.
"""
import time
import logging
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, QTimer

from aesgard.ui import formatDisplayName
from aesgard.web_overlay import update_overlay_timer

logger = logging.getLogger(__name__)


class SessionBarWidget(QFrame):
    """Horizontal bar indicating active gameplay session and live stopwatch."""
    def __init__(self, dashboard, parent=None):
        super().__init__(parent)
        self.dashboard = dashboard
        self.sessionStartTime = None
        self.activePlayingGame = None
        self.sessionTimer = QTimer(self)
        self.sessionTimer.setInterval(1000)
        self.sessionTimer.timeout.connect(self._onSessionTimerTick)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f1c2b, stop:0.5 #091724, stop:1 #064e3b);
                border: 2px solid #10b981;
                border-radius: 10px;
                padding: 6px 14px;
            }
        """)
        sLayout = QHBoxLayout(self)
        sLayout.setContentsMargins(8, 4, 8, 4)
        sLayout.setSpacing(12)

        self.lblSessionStatus = QLabel("🐺 CAÇADA / GAMEPLAY ATIVA:")
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
        self.hide()

    def startGameplaySession(self, gameEntry):
        self.activePlayingGame = gameEntry
        self.sessionStartTime = time.time()
        name = formatDisplayName(gameEntry)
        self.lblSessionGame.setText(name)
        self.lblSessionTime.setText("⏱️ 00:00:00")
        self.show()
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
            self.hide()
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
        self.hide()
        update_overlay_timer("00:00:00")

        # Save to Live History automatically
        mgr = getattr(self.dashboard, 'liveHistoryMgr', None)
        if mgr:
            mgr.recordLive(
                gameName=game_name,
                durationHours=duration_hours,
                notes=f"Sessão de gameplay ({minutes} minutos) finalizada pelo streamer"
            )
        if hasattr(self.dashboard, 'refreshLiveHistoryTable'):
            self.dashboard.refreshLiveHistoryTable()

        QMessageBox.information(
            self,
            "Sessão Finalizada",
            f"<b>Sessão de gameplay gravada com sucesso!</b><br><br>"
            f"• Jogo: <b>{display_name}</b><br>"
            f"• Duração: <font color='#00cec9'><b>{minutes} minutos ({duration_hours}h)</b></font><br><br>"
            f"O registro foi adicionado automaticamente ao seu Histórico de Lives."
        )
