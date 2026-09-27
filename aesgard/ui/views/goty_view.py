# -*- coding: utf-8 -*-
"""
Game of the Year (GOTY) Hall of Fame View Component for Canino Gaming.
Features a Klondike Gold spotlight card and historical explorer table (1983 - 2025).
"""
import logging
import webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QImage, QColor

from aesgard.database import getRandomGoty, getAllGotys
from aesgard.gameutil import executeGame, findGameIcon
from aesgard.intel_dialog import GameIntelDialog
from aesgard.sound import get_sound_manager

logger = logging.getLogger(__name__)


class GotyView(QWidget):
    """View container for GOTY Hall of Fame (Ouro de Klondike)."""
    def __init__(self, dashboard, parent=None):
        super().__init__(parent)
        self.dashboard = dashboard
        self.currentGoty = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
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
        self.gotyYearBadge = QLabel("🏆 OURO DE KLONDIKE • GOTY DO ANO 2024")
        self.gotyYearBadge.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.gotyYearBadge.setStyleSheet("color: #fbbf24; letter-spacing: 1px;")
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
        self.btnGotyReroll.clicked.connect(lambda: self.onRerollGoty(initial=False))
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

    def onRerollGoty(self, initial=False):
        if not initial:
            get_sound_manager().play("pack_victory")
        goty = getRandomGoty()
        if not goty:
            return
        self.currentGoty = goty
        if hasattr(self.dashboard, 'currentGoty'):
            self.dashboard.currentGoty = goty
        self.updateGotyDisplay(goty)

    def updateGotyDisplay(self, goty):
        if not goty:
            return
        self.gotyYearBadge.setText(f"🏆 OURO DE KLONDIKE • GOTY DO ANO {goty['year']}")
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

        try:
            lookup_target = goty.get('library_entry') if goty.get('is_installed') and goty.get('library_entry') else goty['title']
            cfg = getattr(self.dashboard, 'config', None)
            pn_path = getattr(cfg, 'playnitePath', '') if cfg else ''
            pilImg = findGameIcon(lookup_target, playnitePath=pn_path)
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
            if hasattr(self.dashboard, 'startGameplaySession'):
                self.dashboard.startGameplaySession(target)
            self.dashboard.showMinimized()
            executeGame(target, getattr(self.dashboard, 'steamOwnedGames', []))
            if hasattr(self.dashboard, 'refreshStats'):
                self.dashboard.refreshStats()
            if hasattr(self.dashboard, 'refreshTable'):
                self.dashboard.refreshTable()

    def onExploreGoty(self):
        if not self.currentGoty:
            return
        title = self.currentGoty['title']
        url = f"https://www.google.com/search?q={title.replace(' ', '+')}+game"
        webbrowser.open(url)

    def onOpenGotyIntel(self):
        title = self.currentGoty['title'] if self.currentGoty else "GOTY"
        pix = self.gotyImageLabel.pixmap()
        dlg = GameIntelDialog(title, coverPixmap=pix, parent=self)
        dlg.exec()

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
