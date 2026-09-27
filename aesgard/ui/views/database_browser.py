# -*- coding: utf-8 -*-
"""
Database Browser (Território do Banco de Jogos) Component for Canino Gaming.
Features real-time search, status filtering, table sorting, and direct launch.
"""
import logging
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

from aesgard.database import getGamesList, findGameInfo
from aesgard.ui import formatDisplayName, detectPlatform, getPlatformColor
from aesgard.gameutil import executeGame, installGame

logger = logging.getLogger(__name__)


class DatabaseBrowserWidget(QFrame):
    """Component for browsing, searching, and filtering library games."""
    def __init__(self, dashboard, parent=None):
        super().__init__(parent)
        self.dashboard = dashboard
        self._searchTimer = QTimer(self)
        self._searchTimer.setSingleShot(True)
        self._searchTimer.setInterval(250)
        self._searchTimer.timeout.connect(self.refreshTable)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("background-color: #0c1420; border: 1px solid #1c2f44; border-radius: 14px; padding: 14px;")
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header with Search and Filter
        topRow = QHBoxLayout()

        browserTitle = QLabel("📚 TERRITÓRIO DO BANCO DE JOGOS")
        browserTitle.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        browserTitle.setStyleSheet("color: #f0f6fc; letter-spacing: 1px;")
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

    def refreshTable(self):
        query = self.searchBox.text().strip()
        status_filter = self.filterCombo.currentText()
        cfg = getattr(self.dashboard, 'config', None)
        limit = getattr(cfg, 'uiTableLimit', 400) if cfg else 400
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
                    if hasattr(self.dashboard, 'startGameplaySession'):
                        self.dashboard.startGameplaySession(target)
                    self.dashboard.showMinimized()
                    executeGame(target, getattr(self.dashboard, 'steamOwnedGames', []))
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

                if hasattr(self.dashboard, 'refreshStats'):
                    self.dashboard.refreshStats()
                self.refreshTable()
                if hasattr(self.dashboard, 'updateHeroDisplay'):
                    self.dashboard.updateHeroDisplay(target)
        else:
            QMessageBox.information(self, "Aviso", "Por favor, selecione um jogo na tabela primeiro.")

    def onTableDoubleClicked(self, index):
        self.onPlaySelected()
