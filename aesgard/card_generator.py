"""
Social Card Generator for Choose Random Game.
Renders high-resolution 1200x630 PNG images suitable for YouTube Community,
Discord announcements, and Twitter/X posts.
"""

import os
import time
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QImage, QPixmap, QPainter, QColor, QFont, QBrush, QPen, QLinearGradient, QRadialGradient
)

from aesgard.ui import formatDisplayName, detectPlatform
from aesgard.hltb import get_cached_hltb, format_hltb_duration


def generate_live_card(game_str: str,
                       cover_pixmap: QPixmap = None,
                       channel_name: str = "@Hablocher",
                       custom_tag: str = "🎮 JOGO DA LIVE",
                       out_dir: str = "screenshots") -> str:
    """
    Renders a 1200x630 HD promotional card and saves it to out_dir.
    Returns the absolute path of the generated PNG.
    """
    os.makedirs(out_dir, exist_ok=True)
    
    width = 1200
    height = 630
    image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(QColor("#090d16"))

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    # 1. Background gradient with neon ambient glows
    bg_grad = QLinearGradient(0, 0, width, height)
    bg_grad.setColorAt(0.0, QColor("#090d16"))
    bg_grad.setColorAt(0.5, QColor("#0f172a"))
    bg_grad.setColorAt(1.0, QColor("#1e1b4b"))
    painter.fillRect(0, 0, width, height, bg_grad)

    # Radial ambient spot 1 (cyan glow top-left)
    rad1 = QRadialGradient(200, 150, 450)
    rad1.setColorAt(0.0, QColor(6, 182, 212, 50))
    rad1.setColorAt(1.0, QColor(6, 182, 212, 0))
    painter.fillRect(0, 0, width, height, rad1)

    # Radial ambient spot 2 (purple glow bottom-right)
    rad2 = QRadialGradient(1000, 500, 500)
    rad2.setColorAt(0.0, QColor(139, 92, 246, 60))
    rad2.setColorAt(1.0, QColor(139, 92, 246, 0))
    painter.fillRect(0, 0, width, height, rad2)

    # Decorative cyber grid lines / border
    border_pen = QPen(QColor(56, 189, 248, 120), 2)
    painter.setPen(border_pen)
    painter.drawRoundedRect(QRectF(20, 20, width - 40, height - 40), 16, 16)

    # 2. Cover Artwork Presentation (Left Side)
    cover_x = 70
    cover_y = 65
    cover_w = 340
    cover_h = 500

    # Draw Cover Frame shadow / glow
    glow_pen = QPen(QColor("#00f2fe"), 3)
    painter.setPen(glow_pen)
    painter.setBrush(QBrush(QColor("#1e293b")))
    painter.drawRoundedRect(QRectF(cover_x - 3, cover_y - 3, cover_w + 6, cover_h + 6), 14, 14)

    if cover_pixmap and not cover_pixmap.isNull():
        scaled_cover = cover_pixmap.scaled(
            cover_w, cover_h,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        # Crop center
        cx = (scaled_cover.width() - cover_w) // 2
        cy = (scaled_cover.height() - cover_h) // 2
        cropped = scaled_cover.copy(cx, cy, cover_w, cover_h)
        painter.drawPixmap(cover_x, cover_y, cropped)
    else:
        # Placeholder styling
        painter.setPen(QColor("#64748b"))
        painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        painter.drawText(QRectF(cover_x, cover_y, cover_w, cover_h),
                         Qt.AlignmentFlag.AlignCenter, "🎮 CAPA NÃO\nDISPONÍVEL")

    # 3. Typography & Information (Right Side)
    info_x = 450
    curr_y = 75

    # Badge: Live / Next Game Tag
    tag_rect = QRectF(info_x, curr_y, 220, 36)
    tag_grad = QLinearGradient(info_x, curr_y, info_x + 220, curr_y)
    tag_grad.setColorAt(0.0, QColor("#ec4899"))
    tag_grad.setColorAt(1.0, QColor("#8b5cf6"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(tag_grad))
    painter.drawRoundedRect(tag_rect, 18, 18)

    painter.setPen(QColor("#ffffff"))
    painter.setFont(QFont("Segoe UI", 11, QFont.Weight.ExtraBold))
    painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, custom_tag)

    curr_y += 56

    # Game Title
    game_title = formatDisplayName(game_str)
    painter.setPen(QColor("#f8fafc"))
    
    # Adaptive font size based on title length
    if len(game_title) > 35:
        title_font = QFont("Segoe UI", 26, QFont.Weight.Black)
    elif len(game_title) > 22:
        title_font = QFont("Segoe UI", 32, QFont.Weight.Black)
    else:
        title_font = QFont("Segoe UI", 38, QFont.Weight.Black)
    painter.setFont(title_font)

    title_rect = QRectF(info_x, curr_y, 680, 110)
    painter.drawText(title_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, game_title)

    curr_y += 115

    # Platform & Source Badges
    platform_name = detectPlatform(game_str)
    
    # Draw Platform Pill
    plat_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
    painter.setFont(plat_font)
    plat_text = f"🕹️ {platform_name}"
    plat_w = 200
    painter.setBrush(QBrush(QColor("#0f172a")))
    painter.setPen(QPen(QColor("#38bdf8"), 2))
    painter.drawRoundedRect(QRectF(info_x, curr_y, plat_w, 40), 10, 10)
    painter.setPen(QColor("#38bdf8"))
    painter.drawText(QRectF(info_x, curr_y, plat_w, 40), Qt.AlignmentFlag.AlignCenter, plat_text)

    # HLTB Duration Badge
    hltb_data = get_cached_hltb(game_title)
    if hltb_data and hltb_data.get("main_story", 0) > 0:
        main_hours = hltb_data.get("main_story")
        hltb_text = f"⏱️ ~{main_hours:.1f}h (HLTB)"
        hltb_x = info_x + plat_w + 16
        hltb_w = 210
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.setPen(QPen(QColor("#a855f7"), 2))
        painter.drawRoundedRect(QRectF(hltb_x, curr_y, hltb_w, 40), 10, 10)
        painter.setPen(QColor("#c084fc"))
        painter.drawText(QRectF(hltb_x, curr_y, hltb_w, 40), Qt.AlignmentFlag.AlignCenter, hltb_text)

    curr_y += 65

    # Divider bar
    painter.setPen(QPen(QColor("#334155"), 2))
    painter.drawLine(info_x, curr_y, info_x + 680, curr_y)

    curr_y += 25

    # Channel & Community Call-to-action
    painter.setPen(QColor("#94a3b8"))
    painter.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
    painter.drawText(QRectF(info_x, curr_y, 680, 30), Qt.AlignmentFlag.AlignLeft, "Vem acompanhar a gameplay ao vivo no canal!")

    curr_y += 45

    # Channel Branding Pill
    channel_rect = QRectF(info_x, curr_y, 300, 50)
    painter.setBrush(QBrush(QColor(15, 23, 42, 230)))
    painter.setPen(QPen(QColor("#10b981"), 2))
    painter.drawRoundedRect(channel_rect, 12, 12)

    painter.setPen(QColor("#34d399"))
    painter.setFont(QFont("Segoe UI", 15, QFont.Weight.ExtraBold))
    painter.drawText(channel_rect, Qt.AlignmentFlag.AlignCenter, f"📺 {channel_name}")

    # Antigravity / Aesgard Watermark bottom-right
    painter.setPen(QColor("#64748b"))
    painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Normal))
    painter.drawText(QRectF(info_x, 560, 680, 25), Qt.AlignmentFlag.AlignRight, "Powered by Choose Random Game • Aesgard Edition")

    painter.end()

    # Save output
    timestamp = int(time.time())
    safe_title = "".join(c for c in game_title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")[:25]
    filename = f"card_{safe_title}_{timestamp}.png"
    filepath = os.path.abspath(os.path.join(out_dir, filename))
    image.save(filepath, "PNG")
    return filepath
