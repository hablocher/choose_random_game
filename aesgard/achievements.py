# -*- coding: utf-8 -*-
"""
Achievements & Backlog Trophies System for Choose Random Game.
Tracks 12 unlockable gamer badges with SQLite persistence, audio fanfare,
and animated unlock notification popups.
"""
import sqlite3
import logging
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect
from PyQt6.QtGui import QFont, QColor

logger = logging.getLogger(__name__)

ACHIEVEMENTS_ROSTER: Dict[str, Dict] = {
    "first_blood": {
        "key": "first_blood",
        "name": "Primeira Vitória",
        "desc": "Marcou o primeiro jogo como 'Zerado' no banco de dados.",
        "icon": "⚔️"
    },
    "backlog_warrior": {
        "key": "backlog_warrior",
        "name": "Guerreiro do Backlog",
        "desc": "Concluiu 5 jogos da sua biblioteca.",
        "icon": "🛡️"
    },
    "backlog_master": {
        "key": "backlog_master",
        "name": "Mochileiro Lendário",
        "desc": "Concluiu 10 jogos e limpou uma fatia do backlog!",
        "icon": "👑"
    },
    "retro_archaeologist": {
        "key": "retro_archaeologist",
        "name": "Arqueólogo Gamer",
        "desc": "Jogou 5 títulos clássicos de MS-DOS / eXoDOS.",
        "icon": "📜"
    },
    "marathoner": {
        "key": "marathoner",
        "name": "Maratonista de Live",
        "desc": "Jogou por mais de 2 horas contínuas em uma única sessão.",
        "icon": "⏱️"
    },
    "democracy": {
        "key": "democracy",
        "name": "A Voz do Povo",
        "desc": "Jogou um título eleito pelo chat na votação trio.",
        "icon": "🗳️"
    },
    "mystery_solver": {
        "key": "mystery_solver",
        "name": "Mestre do Mistério",
        "desc": "Revelou 3 títulos utilizando o Modo Misterioso.",
        "icon": "🕵️"
    },
    "roulette_addict": {
        "key": "roulette_addict",
        "name": "Amante da Roleta",
        "desc": "Girou a roleta de sorteio pelo menos 20 vezes.",
        "icon": "🎲"
    },
    "speedy": {
        "key": "speedy",
        "name": "Relâmpago",
        "desc": "Concluiu um jogo curto com campanha inferior a 5 horas.",
        "icon": "⚡"
    },
    "goty_connoisseur": {
        "key": "goty_connoisseur",
        "name": "Gosto Refinado",
        "desc": "Sorteou e jogou um vencedor histórico do Game of the Year.",
        "icon": "🏆"
    },
    "challenger": {
        "key": "challenger",
        "name": "Sem Medo do Perigo",
        "desc": "Ativou e encarou um Desafio da Live durante a transmissão.",
        "icon": "💀"
    },
    "bingo_champion": {
        "key": "bingo_champion",
        "name": "Campeão do Bingo",
        "desc": "Completou com sucesso uma linha na cartela do Bingo da Live.",
        "icon": "🎯"
    }
}


def _get_db_path() -> str:
    from aesgard.database import _resolve_sqlite_db_path
    return _resolve_sqlite_db_path("Games.db")


def init_achievements_db():
    """Initializes Achievements table in Games.db."""
    try:
        conn = sqlite3.connect(_get_db_path())
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Achievements (
                key TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                icon TEXT,
                unlocked INTEGER DEFAULT 0,
                unlocked_at DATETIME
            );
        """)
        for a in ACHIEVEMENTS_ROSTER.values():
            cur.execute("""
                INSERT OR IGNORE INTO Achievements (key, name, description, icon, unlocked)
                VALUES (?, ?, ?, ?, 0)
            """, (a["key"], a["name"], a["desc"], a["icon"]))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Error initializing Achievements table: {e}")


def unlock_achievement(key: str, parent_widget=None) -> bool:
    """
    Unlocks an achievement if not already earned.
    Plays audio jingle and triggers popup banner. Returns True if newly unlocked.
    """
    if key not in ACHIEVEMENTS_ROSTER:
        return False

    init_achievements_db()
    try:
        conn = sqlite3.connect(_get_db_path())
        cur = conn.cursor()
        cur.execute("SELECT unlocked FROM Achievements WHERE key = ?", (key,))
        row = cur.fetchone()
        if row and row[0] == 1:
            conn.close()
            return False

        cur.execute("""
            UPDATE Achievements 
            SET unlocked = 1, unlocked_at = CURRENT_TIMESTAMP 
            WHERE key = ?
        """, (key,))
        conn.commit()
        conn.close()

        # Play sound fanfare
        try:
            from aesgard.sound import get_sound_manager
            get_sound_manager().play("achievement")
        except Exception:
            pass

        # Show Toast Notification
        data = ACHIEVEMENTS_ROSTER[key]
        if parent_widget:
            show_achievement_toast(data["name"], data["desc"], data["icon"], parent_widget)

        logger.info(f"🏆 Achievement unlocked: {data['name']}!")
        return True

    except Exception as e:
        logger.warning(f"Error unlocking achievement {key}: {e}")
        return False


def get_all_achievements() -> List[Dict]:
    """Retrieves all achievements with unlocked status and timestamps."""
    init_achievements_db()
    results = []
    try:
        conn = sqlite3.connect(_get_db_path())
        cur = conn.cursor()
        cur.execute("SELECT key, name, description, icon, unlocked, unlocked_at FROM Achievements")
        rows = cur.fetchall()
        conn.close()

        unlocked_map = {r[0]: (bool(r[4]), r[5]) for r in rows}
        for k, a in ACHIEVEMENTS_ROSTER.items():
            is_unlocked, un_at = unlocked_map.get(k, (False, None))
            results.append({
                "key": k,
                "name": a["name"],
                "desc": a["desc"],
                "icon": a["icon"],
                "unlocked": is_unlocked,
                "unlocked_at": un_at
            })
    except Exception as e:
        logger.warning(f"Error reading achievements: {e}")
        for a in ACHIEVEMENTS_ROSTER.values():
            results.append({**a, "unlocked": False, "unlocked_at": None})
    return results


def show_achievement_toast(title: str, desc: str, icon: str, parent: QWidget):
    """Displays a sleek floating notification in the bottom right of parent window."""
    toast = QFrame(parent)
    toast.setStyleSheet("""
        QFrame {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e1b4b, stop:1 #312e81);
            border: 2px solid #818cf8;
            border-radius: 12px;
            color: #ffffff;
        }
    """)
    t_layout = QHBoxLayout(toast)
    t_layout.setContentsMargins(14, 10, 16, 10)
    t_layout.setSpacing(12)

    icon_lbl = QLabel(icon)
    icon_lbl.setFont(QFont("Segoe UI", 26))
    t_layout.addWidget(icon_lbl)

    text_col = QVBoxLayout()
    header_lbl = QLabel("🏆 CONQUISTA DESBLOQUEADA!")
    header_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
    header_lbl.setStyleSheet("color: #a5b4fc;")
    text_col.addWidget(header_lbl)

    name_lbl = QLabel(title)
    name_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
    name_lbl.setStyleSheet("color: #ffffff;")
    text_col.addWidget(name_lbl)

    desc_lbl = QLabel(desc)
    desc_lbl.setFont(QFont("Segoe UI", 10))
    desc_lbl.setStyleSheet("color: #cbd5e1;")
    text_col.addWidget(desc_lbl)
    t_layout.addLayout(text_col)

    toast.adjustSize()
    # Position in bottom-right corner
    p_w = parent.width()
    p_h = parent.height()
    t_w = max(340, toast.width())
    t_h = toast.height()
    toast.setGeometry(p_w - t_w - 24, p_h - t_h - 24, t_w, t_h)
    toast.show()

    # Automatically fade/close after 4.5 seconds
    QTimer.singleShot(4500, toast.deleteLater)


class AchievementsDialog(QDialog):
    """Modern gallery of all 12 Backlog Trophies."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🏆 Troféus & Conquistas do Backlog")
        self.setFixedSize(680, 580)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("background-color: #090d16; color: #ffffff;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        achievements = get_all_achievements()
        unlocked_count = sum(1 for a in achievements if a["unlocked"])

        # Header
        h_row = QHBoxLayout()
        title = QLabel(f"🏆 TROFÉUS DO BACKLOG ({unlocked_count}/{len(achievements)})")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #38bdf8;")
        h_row.addWidget(title)
        h_row.addStretch()

        close_btn = QPushButton("✕ Fechar")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b; color: #cbd5e1;
                border: 1px solid #334155; border-radius: 6px; padding: 6px 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #334155; color: #ffffff; }
        """)
        close_btn.clicked.connect(self.accept)
        h_row.addWidget(close_btn)
        layout.addLayout(h_row)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        c_layout = QGridLayout(container)
        c_layout.setSpacing(12)

        for i, a in enumerate(achievements):
            card = QFrame()
            card.setFixedHeight(95)
            if a["unlocked"]:
                card.setStyleSheet("""
                    QFrame {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e1b4b, stop:1 #1e293b);
                        border: 2px solid #818cf8;
                        border-radius: 10px;
                        padding: 8px;
                    }
                """)
                icon_color = "#ffffff"
                status_text = f"✔ Desbloqueado: {str(a.get('unlocked_at', ''))[:10]}"
                status_color = "#34d399"
            else:
                card.setStyleSheet("""
                    QFrame {
                        background-color: #0f172a;
                        border: 1px solid #1e293b;
                        border-radius: 10px;
                        padding: 8px;
                    }
                """)
                icon_color = "#475569"
                status_text = "🔒 Bloqueado"
                status_color = "#64748b"

            card_layout = QHBoxLayout(card)
            card_layout.setSpacing(12)

            icon_lbl = QLabel(a["icon"] if a["unlocked"] else "🔒")
            icon_lbl.setFont(QFont("Segoe UI", 24))
            card_layout.addWidget(icon_lbl)

            col = QVBoxLayout()
            col.setSpacing(2)
            n_lbl = QLabel(a["name"])
            n_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            n_lbl.setStyleSheet(f"color: {'#ffffff' if a['unlocked'] else '#94a3b8'};")
            col.addWidget(n_lbl)

            d_lbl = QLabel(a["desc"])
            d_lbl.setFont(QFont("Segoe UI", 9))
            d_lbl.setStyleSheet("color: #cbd5e1;")
            d_lbl.setWordWrap(True)
            col.addWidget(d_lbl)

            s_lbl = QLabel(status_text)
            s_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            s_lbl.setStyleSheet(f"color: {status_color};")
            col.addWidget(s_lbl)

            card_layout.addLayout(col)
            card_layout.setStretch(1, 1)

            row, c = divmod(i, 2)
            c_layout.addWidget(card, row, c)

        scroll.setWidget(container)
        layout.addWidget(scroll)
