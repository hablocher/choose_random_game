"""
Wheel of Fortune (Roda da Fortuna) dialog for Choose Random Game.
Provides an interactive spinning wheel with smooth deceleration animation,
tick sounds (optional / visual ticks), and custom candidate slices.
"""

import math
import random
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import (
    QColor, QPainter, QBrush, QPen, QFont, QPainterPath, QLinearGradient, QPolygonF
)
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QGraphicsDropShadowEffect
)

from aesgard.ui import formatDisplayName, detectPlatform


class SpinningWheelWidget(QWidget):
    """Custom QWidget that draws a segmented spinning wheel with ease-out animation."""
    spinFinished = pyqtSignal(str)

    # Vibrant cyberpunk / retro-synth palette for wheel slices
    PALETTE = [
        QColor("#e81cff"), QColor("#40c9ff"), QColor("#ff007f"), QColor("#00f2fe"),
        QColor("#fee140"), QColor("#fa709a"), QColor("#30cfd0"), QColor("#330867"),
        QColor("#f857a6"), QColor("#ff5858"), QColor("#667eea"), QColor("#764ba2")
    ]

    def __init__(self, candidates: list[str], parent=None):
        super().__init__(parent)
        self.candidates = candidates if candidates else ["Jogo 1", "Jogo 2", "Jogo 3"]
        self.angle = 0.0  # Current rotation angle in degrees
        self.angular_velocity = 0.0
        self.is_spinning = False
        self.setMinimumSize(440, 440)

        # Animation timer (approx 60 FPS)
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._step_spin)

    def start_spin(self):
        if self.is_spinning:
            return
        self.is_spinning = True
        # Random initial velocity between 28 and 42 degrees/frame + extra spins
        self.angular_velocity = random.uniform(28.0, 42.0)
        self.timer.start()

    def _step_spin(self):
        if self.angular_velocity > 0.08:
            self.angle = (self.angle + self.angular_velocity) % 360.0
            # Exponential ease-out damping
            self.angular_velocity *= 0.982
            self.update()
        else:
            # Stopped
            self.angular_velocity = 0.0
            self.timer.stop()
            self.is_spinning = False
            self.update()
            winner = self.get_selected_game()
            self.spinFinished.emit(winner)

    def get_selected_game(self) -> str:
        """The indicator arrow is at the top (270 degrees in Qt coordinates, or 90 deg from top).
        Qt drawPie starts at 3 o'clock (0 deg) and goes counter-clockwise.
        Top is at 90 degrees (or -270).
        """
        n = len(self.candidates)
        if n == 0:
            return ""
        slice_angle = 360.0 / n
        # Top pointer is at 90 degrees. Normalize relative to current rotation
        pointer_deg = 90.0
        rel_deg = (pointer_deg - self.angle) % 360.0
        idx = int(rel_deg // slice_angle) % n
        return self.candidates[idx]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w = self.width()
        h = self.height()
        size = min(w, h) - 40
        center_x = w / 2.0
        center_y = h / 2.0
        radius = size / 2.0

        n = len(self.candidates)
        slice_angle = 360.0 / n if n > 0 else 360.0

        # Draw outer glowing ring
        ring_pen = QPen(QColor("#00f2fe"), 6)
        painter.setPen(ring_pen)
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawEllipse(QPointF(center_x, center_y), radius + 8, radius + 8)

        # Outer rim bolts
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#38bdf8")))
        for i in range(16):
            bolt_deg = math.radians(i * (360 / 16))
            bx = center_x + (radius + 8) * math.cos(bolt_deg)
            by = center_y + (radius + 8) * math.sin(bolt_deg)
            painter.drawEllipse(QPointF(bx, by), 3, 3)
        painter.restore()

        # Draw Wheel Slices
        rect = QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2)

        for i, cand in enumerate(self.candidates):
            start_deg = (self.angle + i * slice_angle) % 360.0
            color = self.PALETTE[i % len(self.PALETTE)]
            
            # Subtle gradient for 3D slice effect
            slice_path = QPainterPath()
            slice_path.moveTo(center_x, center_y)
            slice_path.arcTo(rect, start_deg, slice_angle)
            slice_path.closeSubpath()

            painter.setPen(QPen(QColor("#090d16"), 2))
            painter.setBrush(QBrush(color))
            painter.drawPath(slice_path)

            # Draw candidate label along slice radius
            painter.save()
            mid_deg = math.radians(start_deg + slice_angle / 2.0)
            painter.translate(center_x, center_y)
            painter.rotate(- (start_deg + slice_angle / 2.0))

            label = formatDisplayName(cand)
            if len(label) > 18:
                label = label[:16] + ".."

            painter.setPen(QColor("#ffffff"))
            font = QFont("Segoe UI", 9, QFont.Weight.Bold)
            painter.setFont(font)
            # Text position along the arm
            text_rect = QRectF(radius * 0.35, -12, radius * 0.58, 24)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, label)
            painter.restore()

        # Center Hub (metallic dome)
        hub_radius = radius * 0.22
        hub_grad = QLinearGradient(center_x - hub_radius, center_y - hub_radius, center_x + hub_radius, center_y + hub_radius)
        hub_grad.setColorAt(0.0, QColor("#334155"))
        hub_grad.setColorAt(0.5, QColor("#0f172a"))
        hub_grad.setColorAt(1.0, QColor("#1e293b"))

        painter.setPen(QPen(QColor("#00f2fe"), 3))
        painter.setBrush(QBrush(hub_grad))
        painter.drawEllipse(QPointF(center_x, center_y), hub_radius, hub_radius)

        # Center neon icon / text
        painter.setPen(QColor("#38bdf8"))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.ExtraBold))
        painter.drawText(QRectF(center_x - hub_radius, center_y - hub_radius, hub_radius * 2, hub_radius * 2),
                         Qt.AlignmentFlag.AlignCenter, "⚡")

        # Pointer Arrow at Top (pointing down into the rim)
        pointer = QPolygonF([
            QPointF(center_x, center_y - radius + 10),       # Tip pointing down
            QPointF(center_x - 14, center_y - radius - 16), # Left ear
            QPointF(center_x + 14, center_y - radius - 16)  # Right ear
        ])
        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.setBrush(QBrush(QColor("#ef4444")))
        painter.drawPolygon(pointer)


class WheelOfFortuneDialog(QDialog):
    """Modern modal dialog containing the spinning wheel and selection controls."""

    def __init__(self, candidates: list[str], parent=None):
        super().__init__(parent)
        self.candidates = candidates
        self.winner = None
        self.setWindowTitle("🎡 Roda da Fortuna Gamer - Sorteio ao Vivo")
        self.setFixedSize(520, 640)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #090d16, stop:0.5 #0f172a, stop:1 #1e1b4b);
            }
        """)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        # Header
        title = QLabel("🎡 RODA DA FORTUNA GAMER")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: 900; color: #38bdf8; letter-spacing: 1px;")
        layout.addWidget(title)

        subtitle = QLabel("Gire a roda e deixe o destino escolher o próximo jogo da live!")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 11px; color: #94a3b8;")
        layout.addWidget(subtitle)

        # Wheel Widget
        self.wheel = SpinningWheelWidget(self.candidates, self)
        self.wheel.spinFinished.connect(self._on_spin_finished)
        layout.addWidget(self.wheel, alignment=Qt.AlignmentFlag.AlignCenter)

        # Result display
        self.lbl_result = QLabel("Clique no botão abaixo para girar!")
        self.lbl_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_result.setStyleSheet("""
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 8px;
            font-size: 13px;
            font-weight: bold;
            color: #f8fafc;
        """)
        layout.addWidget(self.lbl_result)

        # Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)

        self.btn_spin = QPushButton("⚡ GIRAR RODA!")
        self.btn_spin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_spin.setFixedHeight(44)
        self.btn_spin.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #06b6d4);
                color: #ffffff;
                font-weight: 900;
                font-size: 14px;
                border-radius: 10px;
                border: none;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a78bfa, stop:1 #22d3ee);
            }
            QPushButton:disabled {
                background: #475569;
                color: #94a3b8;
            }
        """)
        self.btn_spin.clicked.connect(self._start_spin)
        btn_box.addWidget(self.btn_spin)

        self.btn_choose = QPushButton("🎮 Jogar Este")
        self.btn_choose.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_choose.setFixedHeight(44)
        self.btn_choose.setEnabled(False)
        self.btn_choose.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: #ffffff;
                font-weight: 900;
                font-size: 13px;
                border-radius: 10px;
                border: none;
                padding: 0 16px;
            }
            QPushButton:hover {
                background: #059669;
            }
            QPushButton:disabled {
                background: #334155;
                color: #64748b;
            }
        """)
        self.btn_choose.clicked.connect(self.accept)
        btn_box.addWidget(self.btn_choose)

        layout.addLayout(btn_box)

    def _start_spin(self):
        self.btn_spin.setEnabled(False)
        self.btn_choose.setEnabled(False)
        self.lbl_result.setText("🌀 Girando a roda...")
        self.lbl_result.setStyleSheet("""
            background: rgba(30, 41, 59, 0.9);
            border: 1px solid #00f2fe;
            border-radius: 8px;
            padding: 8px;
            font-size: 13px;
            font-weight: bold;
            color: #38bdf8;
        """)
        self.wheel.start_spin()

    def _on_spin_finished(self, winner: str):
        self.winner = winner
        self.btn_spin.setEnabled(True)
        self.btn_spin.setText("🔄 Girar Novamente")
        self.btn_choose.setEnabled(True)
        name = formatDisplayName(winner)
        plat = detectPlatform(winner)
        self.lbl_result.setText(f"🎉 VENCEDOR: {name} [{plat}]")
        self.lbl_result.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(16, 185, 129, 0.2), stop:1 rgba(6, 182, 212, 0.2));
            border: 2px solid #10b981;
            border-radius: 8px;
            padding: 8px;
            font-size: 14px;
            font-weight: 900;
            color: #34d399;
        """)

    def get_winner(self) -> str | None:
        return self.winner
