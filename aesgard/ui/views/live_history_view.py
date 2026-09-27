# -*- coding: utf-8 -*-
"""
Live History (Trilhas Percorridas) View Component for Canino Gaming.
Displays chronological records of past broadcasts with durations, notes, and channel links.
"""
import webbrowser
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from aesgard.ui import formatDisplayName
from aesgard.ui.theme import extractChannelHandle

logger = logging.getLogger(__name__)


class LiveHistoryView(QWidget):
    """View container for Trilhas Percorridas (Broadcast History)."""
    def __init__(self, dashboard, parent=None):
        super().__init__(parent)
        self.dashboard = dashboard
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header Bar
        topBar = QHBoxLayout()
        hTitle = QLabel("📜 TRILHAS PERCORRIDAS • HISTÓRICO DE TRANSMISSÕES AO VIVO")
        hTitle.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        hTitle.setStyleSheet("color: #fbbf24; letter-spacing: 1px;")
        topBar.addWidget(hTitle)
        topBar.addStretch()

        self.btnRefreshLiveHistory = QPushButton("🔄 Atualizar")
        self.btnRefreshLiveHistory.setObjectName("BtnSecondary")
        self.btnRefreshLiveHistory.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnRefreshLiveHistory.clicked.connect(self.refreshLiveHistoryTable)
        topBar.addWidget(self.btnRefreshLiveHistory)
        layout.addLayout(topBar)

        # YouTube Channels Showcase Banner (se configurados no .ini)
        cfg = getattr(self.dashboard, 'config', None)
        mainChannelUrl = getattr(cfg, 'streamerYouTubeMainChannel', '').strip() if cfg else ''
        liveChannelUrl = getattr(cfg, 'streamerYouTubeLiveChannel', '').strip() if cfg else ''

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

    def refreshLiveHistoryTable(self):
        mgr = getattr(self.dashboard, 'liveHistoryMgr', None)
        if not mgr:
            return
        records = mgr.getLiveHistory(limit=60)
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
        mgr = getattr(self.dashboard, 'liveHistoryMgr', None)
        choice = getattr(self.dashboard, 'currentChoice', None)
        if not mgr or not choice:
            return
        name = formatDisplayName(choice)
        mgr.recordLive(gameName=choice, notes="Sorteado pelo Canino Gaming")
        QMessageBox.information(self, "Live Gravada!", f"O jogo '{name}' foi registrado com sucesso no histórico de transmissões ao vivo!")
        self.refreshLiveHistoryTable()

    def onAddCustomLiveRecord(self):
        mgr = getattr(self.dashboard, 'liveHistoryMgr', None)
        choice = getattr(self.dashboard, 'currentChoice', None)
        if not mgr or not choice:
            return
        notes = self.liveNotesInput.text().strip() or "Transmissão ao vivo no YouTube"
        mgr.recordLive(gameName=choice, notes=notes)
        self.liveNotesInput.clear()
        self.refreshLiveHistoryTable()
        QMessageBox.information(self, "Registrado!", f"Live com '{formatDisplayName(choice)}' registrada!")

    def onDeleteSelectedLiveRecord(self):
        mgr = getattr(self.dashboard, 'liveHistoryMgr', None)
        if not mgr:
            return
        row = self.liveTable.currentRow()
        if row >= 0:
            id_item = self.liveTable.item(row, 0)
            if id_item:
                live_id = int(id_item.text())
                mgr.deleteLive(live_id)
                self.refreshLiveHistoryTable()
