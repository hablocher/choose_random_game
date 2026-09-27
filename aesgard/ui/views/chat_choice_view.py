# -*- coding: utf-8 -*-
"""
Chat Choice (Escolha da Matilha) View Component for Canino Gaming.
Renders a triple candidate poll for YouTube/Twitch live streams with live voting.
"""
import random
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QApplication, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QImage

from aesgard.gameutil import executeGame, findGameIcon
from aesgard.ui import formatDisplayName, detectPlatform
from aesgard.intel_dialog import GameIntelDialog
from aesgard.web_overlay import update_overlay_poll

logger = logging.getLogger(__name__)


class ChatChoiceView(QWidget):
    """View container for Escolha da Matilha (YouTube/Twitch Chat Choice Poll)."""
    def __init__(self, dashboard, parent=None):
        super().__init__(parent)
        self.dashboard = dashboard
        self.chatChoiceTrio = []
        self.chatVotes = [0, 0, 0]
        self.trioCards = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(14)

        # Header Bar
        header = QHBoxLayout()
        hTitle = QLabel("🐺 ESCOLHA DA MATILHA • ENQUETE AO VIVO DO YOUTUBE")
        hTitle.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        hTitle.setStyleSheet("color: #38bdf8; letter-spacing: 1px;")
        header.addWidget(hTitle)
        header.addStretch()

        self.btnCopyPoll = QPushButton("📋 Copiar Enquete para o Chat")
        self.btnCopyPoll.setObjectName("BtnSecondary")
        self.btnCopyPoll.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnCopyPoll.setToolTip("Copia o texto formatado das 3 opções para abrir a enquete no chat da live")
        self.btnCopyPoll.clicked.connect(self.onCopyChatPoll)
        header.addWidget(self.btnCopyPoll)

        self.btnRerollTrio = QPushButton("🎲 Sortear 3 Novas Presas")
        self.btnRerollTrio.setObjectName("BtnReroll")
        self.btnRerollTrio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnRerollTrio.clicked.connect(self.onRerollChatChoice)
        header.addWidget(self.btnRerollTrio)
        layout.addLayout(header)

        hint = QLabel("💡 Sorteie 3 presas instaladas no seu PC. A matilha no chat vota e você clica em 'JOGAR' no vencedor escolhido!")
        hint.setStyleSheet("color: #8c96a8; font-size: 11px; font-style: italic;")
        layout.addWidget(hint)

        # 3 Cards Container
        self.trioContainer = QHBoxLayout()
        self.trioContainer.setSpacing(16)
        self.trioCards = []

        labels = [
            ("PRESA A (Gélida)", "#38bdf8", "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8)", "#080d14"),
            ("PRESA B (Ouro Klondike)", "#f59e0b", "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #fbbf24)", "#080d14"),
            ("PRESA C (Boreal)", "#10b981", "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #34d399)", "#080d14")
        ]
        for i, (opt_name, color, btn_gradient, btn_text_color) in enumerate(labels):
            card = QFrame()
            card.setObjectName(f"TrioCard_{i}")
            card.setStyleSheet(f"""
                QFrame#TrioCard_{i} {{
                    background-color: #0c1420;
                    border: 2px solid {color};
                    border-radius: 14px;
                    padding: 14px;
                }}
            """)
            cLayout = QVBoxLayout(card)
            cLayout.setSpacing(10)

            # Option Badge
            optBadge = QLabel(opt_name)
            optBadge.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            optBadge.setStyleSheet(f"background-color: {color}; color: #080d14; border-radius: 6px; padding: 4px 12px; font-weight: bold; border: none;")
            optBadge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cLayout.addWidget(optBadge)

            # Cover Box
            imgFrame = QFrame()
            imgFrame.setObjectName(f"TrioImgFrame_{i}")
            imgFrame.setStyleSheet(f"""
                QFrame#TrioImgFrame_{i} {{
                    background-color: #080d14;
                    border: 1px solid #1c2f44;
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

    def onRerollChatChoice(self):
        pool = getattr(self.dashboard, 'content', [])
        if len(pool) < 3:
            candidates = pool * 3
        else:
            candidates = random.sample(pool, 3)

        self.chatChoiceTrio = candidates
        self.chatVotes = [0, 0, 0]

        names = [formatDisplayName(g) for g in candidates]
        update_overlay_poll(names[0], names[1], names[2], 0, 0, 0)

        cfg = getattr(self.dashboard, 'config', None)
        pn_path = getattr(cfg, 'playnitePath', '') if cfg else ''

        for i, game in enumerate(candidates):
            card_info = self.trioCards[i]
            card_info["gameEntry"] = game
            card_info["titleLabel"].setText(formatDisplayName(game))
            plat = detectPlatform(game)
            card_info["metaLabel"].setText(f"Plataforma: {plat}")
            if "lblVoteCount" in card_info:
                card_info["lblVoteCount"].setText("0 votos (0%)")

            try:
                pilImg = findGameIcon(game, playnitePath=pn_path)
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
            if hasattr(self.dashboard, 'startGameplaySession'):
                self.dashboard.startGameplaySession(target)
            self.dashboard.showMinimized()
            executeGame(target, getattr(self.dashboard, 'steamOwnedGames', []))
            if hasattr(self.dashboard, 'refreshStats'):
                self.dashboard.refreshStats()
            if hasattr(self.dashboard, 'refreshTable'):
                self.dashboard.refreshTable()
            if hasattr(self.dashboard, 'updateHeroDisplay'):
                self.dashboard.updateHeroDisplay(target)

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
