# -*- coding: utf-8 -*-
"""
Game Intel & Guide Dialog for Choose Random Game.
Modern dark gamer modal dialog offering:
- Game Synopsis & Storyline
- Direct Walkthrough & Guide Links (GameFAQs, IGN, PCGamingWiki, YouTube)
- HowLongToBeat Campaign Estimates
- Local Manual & Documentation opener (PDF, TXT, DOC)
"""
import os
import webbrowser
from typing import Optional, Dict

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QTextEdit, QScrollArea, QFrame,
    QListWidget, QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QIcon

from aesgard.game_intel import getFullGameIntel
from aesgard.ui import detectPlatform, getPlatformColor

class GameIntelDialog(QDialog):
    def __init__(self, gameEntry: str, coverPixmap: Optional[QPixmap] = None, parent=None):
        super().__init__(parent)
        self.gameEntry = gameEntry
        self.coverPixmap = coverPixmap
        self.intel = getFullGameIntel(gameEntry)

        self.setWindowTitle(f"Informações & Guia: {self.intel['displayTitle']}")
        self.resize(760, 560)
        self.setMinimumSize(680, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #070d14;
                color: #e2ecf5;
            }
            QTabWidget::pane {
                border: 1px solid #1c2f44;
                background-color: #0c1522;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #0d1723;
                color: #8da4b8;
                padding: 10px 18px;
                font-weight: bold;
                font-size: 12px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: #0c1522;
                color: #38bdf8;
                border-bottom: 2px solid #38bdf8;
            }
            QPushButton {
                background-color: #121d2a;
                color: #ffffff;
                border: 1px solid #1f344a;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #273145;
                border-color: #00cec9;
            }
        """)

        self.initUI()

    def initUI(self):
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(14)
        mainLayout.setContentsMargins(20, 20, 20, 20)

        # Header: Cover + Title + Platform
        headerFrame = QFrame()
        headerFrame.setStyleSheet("background-color: #12151d; border: 1px solid #242b3b; border-radius: 12px; padding: 12px;")
        headerLayout = QHBoxLayout(headerFrame)
        headerLayout.setSpacing(16)

        # Cover Thumbnail
        imgLabel = QLabel()
        imgLabel.setFixedSize(100, 115)
        imgLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        imgLabel.setStyleSheet("background-color: #0d0f14; border-radius: 8px;")
        if self.coverPixmap:
            imgLabel.setPixmap(self.coverPixmap.scaled(100, 115, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        headerLayout.addWidget(imgLabel)

        # Details
        infoCol = QVBoxLayout()
        infoCol.setSpacing(4)

        tagRow = QHBoxLayout()
        platform = detectPlatform(self.gameEntry)
        platBadge = QLabel(platform.upper())
        platBadge.setStyleSheet(f"background-color: {getPlatformColor(platform)}; color: #ffffff; border-radius: 4px; padding: 2px 8px; font-weight: bold; font-size: 11px;")
        tagRow.addWidget(platBadge)

        sourceBadge = QLabel(f"FONTE: {self.intel.get('source', 'AUTO')}")
        sourceBadge.setStyleSheet("background-color: #2d3748; color: #a0aec0; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: bold;")
        tagRow.addWidget(sourceBadge)
        tagRow.addStretch()
        infoCol.addLayout(tagRow)

        titleLabel = QLabel(self.intel['displayTitle'])
        titleLabel.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        titleLabel.setStyleSheet("color: #ffffff;")
        titleLabel.setWordWrap(True)
        infoCol.addWidget(titleLabel)

        if self.intel.get('genre'):
            genreLabel = QLabel(f"Gênero / Descrição: {self.intel['genre']}")
            genreLabel.setStyleSheet("color: #00cec9; font-size: 12px;")
            infoCol.addWidget(genreLabel)

        headerLayout.addLayout(infoCol, 1)
        mainLayout.addWidget(headerFrame)

        # Tabs
        self.tabs = QTabWidget()

        # Tab 1: Sinopse & Enredo
        synopsisWidget = QWidget()
        synLayout = QVBoxLayout(synopsisWidget)
        synLayout.setContentsMargins(14, 14, 14, 14)
        
        synText = QTextEdit()
        synText.setReadOnly(True)
        synText.setStyleSheet("background-color: #0d0f14; border: 1px solid #242b3b; color: #cbd5e1; font-size: 13px; line-height: 1.5; padding: 10px;")
        synText.setPlainText(self.intel['summary'])
        synLayout.addWidget(synText)
        self.tabs.addTab(synopsisWidget, "📖 Sinopse & Enredo")

        # Tab 2: Walkthroughs & Detonados (1-Click Streaming Links)
        guidesWidget = QWidget()
        guidesLayout = QVBoxLayout(guidesWidget)
        guidesLayout.setContentsMargins(16, 16, 16, 16)
        guidesLayout.setSpacing(10)

        guidesHint = QLabel("🔗 Links diretos para guias, detonados e dicas rápidas para consultar durante a live:")
        guidesHint.setStyleSheet("color: #a0aec0; font-size: 12px; margin-bottom: 6px;")
        guidesLayout.addWidget(guidesHint)

        gridContainer = QWidget()
        from PyQt6.QtWidgets import QGridLayout
        grid = QGridLayout(gridContainer)
        grid.setSpacing(12)

        links = self.intel['guideLinks']
        btnDefs = [
            ("GameFAQs (Detonados & Guias)", "GameFAQs", "#0984e3"),
            ("IGN Walkthroughs & Maps", "IGN Guides", "#d63031"),
            ("PCGamingWiki (Bugs & Fixes)", "PCGamingWiki", "#00b894"),
            ("HowLongToBeat (Tempo de Jogo)", "HowLongToBeat", "#e17055"),
            ("YouTube Full Walkthrough", "YouTube Walkthrough", "#e84118"),
            ("Speedrun.com (Recordes & Rotas)", "Speedrun.com", "#6c5ce7"),
            ("Google (Dicas em Português)", "Google Dicas", "#fdcb6e")
        ]

        row = 0
        col = 0
        for label, key, color in btnDefs:
            url = links.get(key)
            if url:
                btn = QPushButton(f"🌐  {label}")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #161b26;
                        color: #ffffff;
                        border: 1px solid #2e384d;
                        border-left: 4px solid {color};
                        padding: 10px 14px;
                        font-size: 12px;
                        text-align: left;
                    }}
                    QPushButton:hover {{
                        background-color: #1e2536;
                        border-color: {color};
                    }}
                """)
                btn.clicked.connect(lambda _, u=url: webbrowser.open(u))
                grid.addWidget(btn, row, col)
                col += 1
                if col >= 2:
                    col = 0
                    row += 1

        guidesLayout.addWidget(gridContainer)
        guidesLayout.addStretch()
        self.tabs.addTab(guidesWidget, "🗺️ Detonados & Walkthroughs")

        # Tab 3: Manuais Locais (eXoDOS / DOSBox Docs)
        manualsWidget = QWidget()
        mLayout = QVBoxLayout(manualsWidget)
        mLayout.setContentsMargins(14, 14, 14, 14)
        mLayout.setSpacing(8)

        manuals = self.intel.get('manuals', [])
        if manuals:
            mHint = QLabel(f"📚 Encontrados {len(manuals)} manuais e documentos locais para este jogo:")
            mHint.setStyleSheet("color: #00cec9; font-size: 12px; font-weight: bold;")
            mLayout.addWidget(mHint)

            mList = QListWidget()
            mList.setStyleSheet("background-color: #0d0f14; border: 1px solid #242b3b; color: #ffffff; padding: 6px;")
            for m in manuals:
                item = QListWidgetItem(f"📄 {m['name']} ({m['ext'].upper()})")
                item.setData(Qt.ItemDataRole.UserRole, m['path'])
                mList.addItem(item)
            mLayout.addWidget(mList)

            btnOpenManual = QPushButton("📂 Abrir Documento Selecionado")
            btnOpenManual.clicked.connect(lambda: self.openSelectedManual(mList))
            mLayout.addWidget(btnOpenManual)
        else:
            noManual = QLabel("Nenhum manual em PDF/TXT encontrado na pasta local deste jogo.\nConsulte a aba 'Detonados & Walkthroughs' para acessar guias online.")
            noManual.setAlignment(Qt.AlignmentFlag.AlignCenter)
            noManual.setStyleSheet("color: #718096; font-size: 13px; padding: 40px;")
            mLayout.addWidget(noManual)

        self.tabs.addTab(manualsWidget, "📚 Manuais Locais")

        # Tab 4: HowLongToBeat (Estimativas de Duração da Campanha)
        hltbWidget = QWidget()
        hLayout = QVBoxLayout(hltbWidget)
        hLayout.setContentsMargins(18, 18, 18, 18)
        hLayout.setSpacing(14)

        try:
            from aesgard.hltb import fetch_hltb_data
            hltb_info = fetch_hltb_data(self.intel['cleanTitle'])
        except Exception:
            hltb_info = None

        if hltb_info and any(hltb_info.get(k, 0) > 0 for k in ("main_story", "main_extra", "completionist")):
            hIntro = QLabel(f"⏱️ Estimativas de conclusão baseadas na comunidade HowLongToBeat:")
            hIntro.setStyleSheet("color: #38bdf8; font-size: 13px; font-weight: bold;")
            hLayout.addWidget(hIntro)

            cardsRow = QHBoxLayout()
            cardsRow.setSpacing(12)

            stats = [
                ("História Principal", hltb_info.get("main_story", 0), "#10b981", "⚡"),
                ("História + Extras", hltb_info.get("main_extra", 0), "#06b6d4", "🎯"),
                ("Complecionista (100%)", hltb_info.get("completionist", 0), "#8b5cf6", "🏆"),
                ("Média Geral", hltb_info.get("all_styles", 0), "#f59e0b", "📊")
            ]

            for s_title, s_hours, s_color, s_icon in stats:
                card = QFrame()
                card.setStyleSheet(f"""
                    QFrame {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #161b26, stop:1 #0f141f);
                        border: 1px solid #242b3b;
                        border-top: 3px solid {s_color};
                        border-radius: 10px;
                        padding: 12px;
                    }}
                """)
                cLayout = QVBoxLayout(card)
                cLayout.setSpacing(6)
                cLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                iconLbl = QLabel(s_icon)
                iconLbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                iconLbl.setStyleSheet("font-size: 24px;")
                cLayout.addWidget(iconLbl)

                timeLbl = QLabel(f"{s_hours:.1f}h" if s_hours > 0 else "--")
                timeLbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                timeLbl.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {s_color};")
                cLayout.addWidget(timeLbl)

                subLbl = QLabel(s_title)
                subLbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                subLbl.setStyleSheet("font-size: 11px; color: #94a3b8; font-weight: bold;")
                cLayout.addWidget(subLbl)

                cardsRow.addWidget(card)

            hLayout.addLayout(cardsRow)

            if hltb_info.get("hltb_url"):
                btnHltbWeb = QPushButton("🔗 Ver Ficha Completa no HowLongToBeat.com")
                btnHltbWeb.setCursor(Qt.CursorShape.PointingHandCursor)
                btnHltbWeb.setStyleSheet("background-color: #1e2433; color: #38bdf8; border: 1px solid #0284c7; padding: 10px; border-radius: 8px;")
                btnHltbWeb.clicked.connect(lambda _, u=hltb_info["hltb_url"]: webbrowser.open(u))
                hLayout.addWidget(btnHltbWeb)
        else:
            noHltb = QLabel("Estimativas detalhadas não encontradas no HowLongToBeat para este título.\nVocê ainda pode consultar o link na aba 'Detonados & Walkthroughs'.")
            noHltb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            noHltb.setStyleSheet("color: #718096; font-size: 13px; padding: 40px;")
            hLayout.addWidget(noHltb)

        hLayout.addStretch()
        self.tabs.addTab(hltbWidget, "⏱️ HowLongToBeat")
        mainLayout.addWidget(self.tabs, 1)

        # Bottom Buttons
        bottomRow = QHBoxLayout()
        
        btnCopyTitle = QPushButton("📋 Copiar Título para o Chat")
        btnCopyTitle.setCursor(Qt.CursorShape.PointingHandCursor)
        btnCopyTitle.clicked.connect(self.copyTitleToClipboard)
        bottomRow.addWidget(btnCopyTitle)

        bottomRow.addStretch()

        btnClose = QPushButton("Fechar")
        btnClose.setStyleSheet("background-color: #242b3b; color: #cbd5e1; border: none; padding: 8px 24px;")
        btnClose.clicked.connect(self.accept)
        bottomRow.addWidget(btnClose)

        mainLayout.addLayout(bottomRow)

    def openSelectedManual(self, listWidget: QListWidget):
        curr = listWidget.currentItem()
        if curr:
            path = curr.data(Qt.ItemDataRole.UserRole)
            if os.path.exists(path):
                try:
                    os.startfile(path)
                except Exception as e:
                    QMessageBox.warning(self, "Erro", f"Não foi possível abrir o arquivo:\n{e}")

    def copyTitleToClipboard(self):
        from PyQt6.QtWidgets import QApplication
        cb = QApplication.clipboard()
        if cb:
            cb.setText(self.intel['cleanTitle'])
            QMessageBox.information(self, "Copiado!", f"Título copiado para a área de transferência:\n\n{self.intel['cleanTitle']}")
