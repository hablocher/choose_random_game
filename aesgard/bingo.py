# -*- coding: utf-8 -*-
"""
Live Streamer Backlog Bingo for Choose Random Game.
Generates interactive 3x3 bingo cards with live events, tracks line completions,
and triggers audio fanfares and Web Overlay sync.
"""
import random
import logging
from typing import List, Dict, Set
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QLabel, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

logger = logging.getLogger(__name__)

BINGO_POOL = [
    "Morreu de queda boba",
    "Achou um segredo / Easter Egg",
    "Bug visual ou glitch engraçado",
    "Ficou perdido procurando a rota",
    "Boss derrotado com pouca vida",
    "Chat deu dica certeira",
    "Pulo milimétrico perfeito",
    "Esqueceu de salvar e perdeu algo",
    "Susto genuíno ao vivo",
    "Elogiou a trilha sonora",
    "Jogou granada/magia no próprio pé",
    "Errou o botão e gastou item raro",
    "Diálogo hilário de NPC",
    "Sub / Seguidor novo durante a ação",
    "Descobriu atalho genial",
    "Morreu na primeira tentativa de boss",
    "Ficou 5 min olhando o inventário",
    "Zerou a fase no aperto do tempo",
    "Comentou sobre nostalgia de infância",
    "Chat começou a rir de uma burrada",
    "Acertou um tiro impossível",
    "Parou a gameplay pra admirar o cenário",
    "Fez uma teoria errada sobre o enredo",
    "Pediu opinião do chat para build"
]


class LiveBingoState:
    """Manages the 3x3 bingo grid, marked state, and victory checks."""

    def __init__(self):
        self.cells: List[str] = []
        self.marked: Set[int] = set()
        self.has_won = False
        self.reset()

    def reset(self):
        self.cells = random.sample(BINGO_POOL, 9)
        self.marked = set()
        self.has_won = False

    def toggle_cell(self, index: int) -> bool:
        if index in self.marked:
            self.marked.remove(index)
        else:
            self.marked.add(index)
        return index in self.marked

    def is_cell_marked(self, index: int) -> bool:
        return index in self.marked

    def check_bingo(self) -> bool:
        """Checks for any complete row, column, or diagonal in the 3x3 grid."""
        lines = [
            # Rows
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            # Columns
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            # Diagonals
            [0, 4, 8], [2, 4, 6]
        ]
        for line in lines:
            if all(idx in self.marked for idx in line):
                self.has_won = True
                return True
        self.has_won = False
        return False

    def to_dict(self) -> Dict:
        return {
            "cells": [
                {"index": i, "text": self.cells[i], "marked": i in self.marked}
                for i in range(9)
            ],
            "has_won": self.has_won
        }


_GLOBAL_BINGO = LiveBingoState()


def get_bingo_state() -> LiveBingoState:
    return _GLOBAL_BINGO


class LiveBingoDialog(QDialog):
    """Modern dark theme 3x3 interactive Bingo card dialog for the streamer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 Bingo da Live & Backlog")
        self.setFixedSize(560, 560)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.state = get_bingo_state()
        self.buttons: List[QPushButton] = []
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0f19;
                color: #ffffff;
            }
            QLabel {
                color: #e2e8f0;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        headerRow = QHBoxLayout()
        title = QLabel("🎯 BINGO DA LIVE")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #38bdf8;")
        headerRow.addWidget(title)

        headerRow.addStretch()

        self.btnNewCard = QPushButton("🔄 Nova Cartela")
        self.btnNewCard.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #cbd5e1;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #ffffff;
            }
        """)
        self.btnNewCard.clicked.connect(self.onNewCard)
        headerRow.addWidget(self.btnNewCard)
        layout.addLayout(headerRow)

        subtitle = QLabel("Marque os eventos que acontecerem durante a jogatina para completar uma linha!")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(subtitle)

        # 3x3 Grid
        gridFrame = QFrame()
        gridFrame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 12px;
                padding: 8px;
            }
        """)
        gridLayout = QGridLayout(gridFrame)
        gridLayout.setSpacing(10)

        for i in range(9):
            btn = QPushButton()
            btn.setFixedHeight(110)
            btn.setWordWrap(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("cell_index", i)
            btn.clicked.connect(lambda _, idx=i: self.onCellClicked(idx))
            self.buttons.append(btn)
            row, col = divmod(i, 3)
            gridLayout.addWidget(btn, row, col)

        layout.addWidget(gridFrame)

        # Status Bar
        self.statusLabel = QLabel("Nenhuma linha completa ainda. Boa sorte na live!")
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.statusLabel.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold;")
        layout.addWidget(self.statusLabel)

        self.update_buttons_ui()

    def onCellClicked(self, index: int):
        self.state.toggle_cell(index)
        from aesgard.sound import get_sound_manager
        get_sound_manager().play("click")

        is_bingo = self.state.check_bingo()
        self.update_buttons_ui()

        if is_bingo:
            get_sound_manager().play("victory")
            self.statusLabel.setText("🎉 BINGO COMPLETO! Linha completada com sucesso!")
            self.statusLabel.setStyleSheet("color: #10b981; font-size: 13px; font-weight: bold;")
            
            # Check Achievement
            try:
                from aesgard.achievements import unlock_achievement
                unlock_achievement("bingo_champion", self.parent())
            except Exception as e:
                logger.debug(f"Achievement trigger error: {e}")

    def onNewCard(self):
        self.state.reset()
        self.statusLabel.setText("Nova cartela gerada! Marque os eventos da jogatina.")
        self.statusLabel.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold;")
        self.update_buttons_ui()

    def update_buttons_ui(self):
        for i, btn in enumerate(self.buttons):
            text = self.state.cells[i]
            is_marked = self.state.is_cell_marked(i)
            if is_marked:
                btn.setText(f"✔\n{text}")
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #059669, stop:1 #10b981);
                        color: #ffffff;
                        border: 2px solid #34d399;
                        border-radius: 8px;
                        font-weight: bold;
                        font-size: 11px;
                        padding: 6px;
                    }
                """)
            else:
                btn.setText(text)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1f2937;
                        color: #cbd5e1;
                        border: 1px solid #374151;
                        border-radius: 8px;
                        font-size: 11px;
                        padding: 6px;
                    }
                    QPushButton:hover {
                        background-color: #374151;
                        border-color: #60a5fa;
                        color: #ffffff;
                    }
                """)
