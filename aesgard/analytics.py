# -*- coding: utf-8 -*-
"""
Library Analytics & Backlog Metrics Engine for Choose Random Game.
Computes platform breakdown, completion percentages, total estimated backlog hours,
and renders a modern dark glassmorphic analytics dashboard.
"""
import math
import sqlite3
import logging
from typing import Dict, List, Tuple
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QWidget, QProgressBar
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush

logger = logging.getLogger(__name__)


def _get_db_path() -> str:
    from aesgard.database import _resolve_sqlite_db_path
    return _resolve_sqlite_db_path("Games.db")


def calculate_analytics_data(content: List[str]) -> Dict:
    """Computes all statistical metrics from GamesChoosed and HltbCache."""
    data = {
        "total_games": len(content),
        "installed": 0,
        "uninstalled": 0,
        "finished": 0,
        "favorites": 0,
        "total_plays": 0,
        "backlog_hours": 0.0,
        "platforms": {},
        "top_played": []
    }

    try:
        from aesgard.ui import detectPlatform
        from aesgard.hltb import get_all_cached_durations, clean_title_for_hltb
        from aesgard.ui import formatDisplayName

        durations = get_all_cached_durations()

        conn = sqlite3.connect(_get_db_path())
        cur = conn.cursor()

        cur.execute("SELECT gameName, timesPlayed, finished, favorite, installed FROM GamesChoosed")
        db_rows = {r[0]: (r[1], r[2], r[3], r[4]) for r in cur.fetchall()}

        # Top 5 Most Played
        cur.execute("SELECT gameName, timesPlayed FROM GamesChoosed WHERE timesPlayed > 0 ORDER BY timesPlayed DESC LIMIT 5")
        for r in cur.fetchall():
            data["top_played"].append((formatDisplayName(r[0]), r[1]))

        conn.close()

        for g in content:
            # Platform breakdown
            plat = detectPlatform(g)
            data["platforms"][plat] = data["platforms"].get(plat, 0) + 1

            # DB info
            info = db_rows.get(g)
            if info:
                times_p, fin, fav, inst = info
                data["total_plays"] += (times_p or 0)
                if fin:
                    data["finished"] += 1
                if fav:
                    data["favorites"] += 1
                if inst:
                    data["installed"] += 1
                else:
                    data["uninstalled"] += 1

                # Sum backlog hours if not yet finished
                if not fin:
                    clean = clean_title_for_hltb(formatDisplayName(g)).lower()
                    h = durations.get(clean, 0.0)
                    if not h and ":" in clean:
                        h = durations.get(clean.split(":")[0].strip(), 0.0)
                    data["backlog_hours"] += (h or 0.0)
            else:
                data["installed"] += 1

        if data["total_games"] > 0:
            data["completion_rate"] = (data["finished"] / data["total_games"]) * 100.0
        else:
            data["completion_rate"] = 0.0

    except Exception as e:
        logger.warning(f"Error calculating analytics: {e}")
        data["completion_rate"] = 0.0

    return data


class DonutChartWidget(QWidget):
    """Clean antialiased Donut Chart for platform distribution."""

    def __init__(self, platform_data: Dict[str, int], parent=None):
        super().__init__(parent)
        self.platform_data = platform_data
        self.setFixedSize(220, 220)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        total = sum(self.platform_data.values())
        if total == 0:
            return

        rect = QRectF(20, 20, 180, 180)
        start_angle = 90 * 16

        colors = [
            "#38bdf8", "#818cf8", "#34d399", "#f59e0b",
            "#ec4899", "#a855f7", "#06b6d4", "#64748b"
        ]

        pen = QPen(Qt.PenStyle.NoPen)
        painter.setPen(pen)

        # Draw arcs
        for i, (plat, count) in enumerate(self.platform_data.items()):
            span_angle = int((count / total) * 360 * 16)
            color = QColor(colors[i % len(colors)])
            painter.setBrush(QBrush(color))
            painter.drawPie(rect, start_angle, span_angle)
            start_angle += span_angle

        # Cut out center to create donut
        painter.setBrush(QBrush(QColor("#0d121f")))
        center_rect = QRectF(60, 60, 100, 100)
        painter.drawEllipse(center_rect)

        # Center Text
        painter.setPen(QPen(QColor("#ffffff")))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.drawText(center_rect, Qt.AlignmentFlag.AlignCenter, f"{total:,}\nJOGOS".replace(",", "."))
        painter.end()


class AnalyticsDialog(QDialog):
    """Full-featured Library Analytics & Backlog Metrics Dialog."""

    def __init__(self, content: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Métricas & Estatísticas do Backlog")
        self.setFixedSize(760, 620)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.content = content
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("background-color: #090d16; color: #ffffff;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        data = calculate_analytics_data(self.content)

        # Header
        h_row = QHBoxLayout()
        title = QLabel("📊 ESTATÍSTICAS DA SUA COLEÇÃO")
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

        # Top Metric Cards (3 cards: Total Jogos, Zerados, Horas Restantes)
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        def make_card(label: str, value: str, sub: str, color: str) -> QFrame:
            f = QFrame()
            f.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #111827, stop:1 #1f2937);
                    border: 1px solid #374151;
                    border-radius: 10px;
                    padding: 12px;
                }}
            """)
            c_l = QVBoxLayout(f)
            c_l.setSpacing(4)
            lbl = QLabel(label)
            lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            lbl.setStyleSheet("color: #94a3b8;")
            c_l.addWidget(lbl)

            val = QLabel(value)
            val.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
            val.setStyleSheet(f"color: {color};")
            c_l.addWidget(val)

            sub_lbl = QLabel(sub)
            sub_lbl.setFont(QFont("Segoe UI", 8))
            sub_lbl.setStyleSheet("color: #64748b;")
            c_l.addWidget(sub_lbl)
            return f

        cards_row.addWidget(make_card("TOTAL NA BIBLIOTECA", f"{data['total_games']:,}".replace(",", "."), f"{data['installed']} instalados • {data['uninstalled']} na nuvem", "#38bdf8"))
        cards_row.addWidget(make_card("JOGOS ZERADOS", f"{data['finished']:,} ({data['completion_rate']:.1f}%)".replace(",", "."), f"{data['favorites']} marcados como favoritos", "#34d399"))
        cards_row.addWidget(make_card("ESTIMATIVA DE BACKLOG", f"~{int(data['backlog_hours']):,}h".replace(",", "."), "Horas de campanha pendentes (HLTB)", "#f59e0b"))
        layout.addLayout(cards_row)

        # Middle Section: Donut Chart + Platform breakdown + Top Played
        mid_row = QHBoxLayout()
        mid_row.setSpacing(16)

        # Left: Donut Chart Widget
        chart_card = QFrame()
        chart_card.setStyleSheet("background-color: #0d121f; border: 1px solid #1e293b; border-radius: 12px; padding: 12px;")
        chart_layout = QVBoxLayout(chart_card)
        chart_title = QLabel("DISTRIBUIÇÃO POR PLATAFORMA")
        chart_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        chart_title.setStyleSheet("color: #cbd5e1;")
        chart_layout.addWidget(chart_title)

        donut = DonutChartWidget(data["platforms"])
        chart_layout.addWidget(donut, alignment=Qt.AlignmentFlag.AlignCenter)
        mid_row.addWidget(chart_card)

        # Right: Platform legend & Top Played
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        # Top Played Card
        top_card = QFrame()
        top_card.setStyleSheet("background-color: #0d121f; border: 1px solid #1e293b; border-radius: 12px; padding: 12px;")
        top_layout = QVBoxLayout(top_card)
        top_title = QLabel("🏆 TOP 5 MAIS JOGADOS")
        top_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        top_title.setStyleSheet("color: #cbd5e1;")
        top_layout.addWidget(top_title)

        if data["top_played"]:
            for name, plays in data["top_played"]:
                p_row = QHBoxLayout()
                n_lbl = QLabel(name[:30] + ("..." if len(name) > 30 else ""))
                n_lbl.setStyleSheet("color: #e2e8f0; font-size: 11px;")
                p_lbl = QLabel(f"{plays}x")
                p_lbl.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")
                p_row.addWidget(n_lbl)
                p_row.addStretch()
                p_row.addWidget(p_lbl)
                top_layout.addLayout(p_row)
        else:
            empty_lbl = QLabel("Nenhum histórico de jogatina registrado ainda.")
            empty_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
            top_layout.addWidget(empty_lbl)

        right_col.addWidget(top_card)

        # Platform Legend Pills
        plat_card = QFrame()
        plat_card.setStyleSheet("background-color: #0d121f; border: 1px solid #1e293b; border-radius: 12px; padding: 12px;")
        plat_layout = QVBoxLayout(plat_card)
        plat_title = QLabel("🏷️ PLATAFORMAS DETECTADAS")
        plat_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        plat_title.setStyleSheet("color: #cbd5e1;")
        plat_layout.addWidget(plat_title)

        p_grid = QGridLayout()
        p_grid.setSpacing(8)
        sorted_plats = sorted(data["platforms"].items(), key=lambda x: x[1], reverse=True)[:8]
        for idx, (p_name, count) in enumerate(sorted_plats):
            p_lbl = QLabel(f"• {p_name}: <b>{count}</b>")
            p_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px;")
            r, c = divmod(idx, 2)
            p_grid.addWidget(p_lbl, r, c)
        plat_layout.addLayout(p_grid)

        right_col.addWidget(plat_card)
        mid_row.addLayout(right_col)
        mid_row.setStretch(1, 1)

        layout.addLayout(mid_row)
