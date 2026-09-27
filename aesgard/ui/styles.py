# -*- coding: utf-8 -*-
"""
Caninos Brancos (White Fang) & Arctic Wild QSS Stylesheet.
Unified design system for Canino Gaming:
- Yukon Night palette (#070d14, #091018, #101a26)
- Glacial Cyan accents (#38bdf8, #0284c7)
- Klondike Gold (#f59e0b) and Boreal Aurora Emerald (#10b981)
- Frosted glass cards with semi-transparency for background art visibility
"""

STYLESHEET = """
QMainWindow {
    background-color: #070d14;
}

QWidget {
    font-family: 'Segoe UI', -apple-system, Arial, sans-serif;
    color: #e2ecf5;
}

/* Header & Outpost Stat Cards */
QFrame#StatCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(16, 26, 38, 220), stop:1 rgba(9, 16, 24, 230));
    border: 1px solid #1c3247;
    border-radius: 10px;
    padding: 6px 8px;
}

QLabel#StatValue {
    font-size: 20px;
    font-weight: bold;
    color: #38bdf8;
}

QLabel#StatLabel {
    font-size: 10px;
    color: #8da4b8;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* Yukon Nav Tabs */
QPushButton.NavBtn {
    background-color: rgba(13, 21, 33, 225);
    border: 1px solid #1a2c3f;
    border-radius: 8px;
    color: #94a9be;
    font-size: 12px;
    font-weight: bold;
    padding: 7px 12px;
}
QPushButton.NavBtn:hover {
    background-color: #142234;
    color: #f0f6fc;
    border-color: #2b4563;
}
QPushButton.NavBtn:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:0.5 #0369a1, stop:1 #0f766e);
    color: #ffffff;
    border-color: #38bdf8;
}

/* Boreal Hero Card */
QFrame#HeroCard {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(15, 28, 44, 215), stop:0.6 rgba(10, 19, 30, 225), stop:1 rgba(7, 13, 20, 235));
    border: 1px solid #1f3b58;
    border-radius: 14px;
    padding: 18px;
}

/* Instinto Selvagem (Game of the Day) Card */
QFrame#GotdCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(14, 39, 62, 220), stop:0.5 rgba(9, 26, 42, 230), stop:1 rgba(6, 16, 26, 240));
    border: 1px solid #38bdf8;
    border-radius: 16px;
    padding: 24px;
}

/* Ouro de Klondike (GOTY) Card */
QFrame#GotyCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(43, 28, 11, 225), stop:0.5 rgba(25, 16, 6, 235), stop:1 rgba(13, 8, 3, 245));
    border: 1px solid #f59e0b;
    border-radius: 16px;
    padding: 24px;
}

/* Yukon / Arctic Themed Popup Menu */
QMenu {
    background-color: #0c1420;
    color: #e2ecf5;
    border: 1px solid #1c3247;
    border-radius: 8px;
    padding: 6px;
}
QMenu::item {
    padding: 7px 22px 7px 12px;
    border-radius: 4px;
    font-size: 12px;
}
QMenu::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0369a1);
    color: #ffffff;
}
QMenu::separator {
    height: 1px;
    background: #1c3247;
    margin: 4px 8px;
}

QLabel#GameTitle {
    font-size: 18px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#PlatformBadge {
    background-color: #1a2a3e;
    color: #94a9be;
    border: 1px solid #233b54;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: bold;
}

/* Action Buttons */
QPushButton#BtnPlay {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:0.5 #0ea5e9, stop:1 #10b981);
    color: #ffffff;
    font-size: 14px;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 12px 20px;
}
QPushButton#BtnPlay:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369a1, stop:0.5 #38bdf8, stop:1 #34d399);
}
QPushButton#BtnPlay:pressed {
    background: #0284c7;
}

QPushButton#BtnReroll {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e3a8a, stop:0.5 #2563eb, stop:1 #0284c7);
    color: #ffffff;
    font-size: 13px;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
}
QPushButton#BtnReroll:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #38bdf8);
}

QPushButton#BtnGoty {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #b45309, stop:0.5 #d97706, stop:1 #f59e0b);
    color: #0e0903;
    font-size: 14px;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 12px 22px;
}
QPushButton#BtnGoty:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #fbbf24);
}

QPushButton#BtnSecondary {
    background-color: #121d2a;
    border: 1px solid #1f344a;
    color: #c8daea;
    font-size: 11px;
    font-weight: 600;
    border-radius: 6px;
    padding: 5px 9px;
}
QPushButton#BtnSecondary:hover {
    background-color: #1a2c3f;
    border-color: #38bdf8;
    color: #ffffff;
}

QPushButton#BtnConfig {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369a1, stop:0.5 #0284c7, stop:1 #0f766e);
    border: 1px solid #38bdf8;
    color: #ffffff;
    font-size: 11px;
    font-weight: bold;
    border-radius: 6px;
    padding: 5px 12px;
}
QPushButton#BtnConfig:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
}

/* Inputs & Combos */
QLineEdit {
    background-color: #0c1420;
    border: 1px solid #1c2f44;
    border-radius: 8px;
    padding: 8px 12px;
    color: #ffffff;
    font-size: 13px;
}
QLineEdit:focus {
    border-color: #38bdf8;
}

QComboBox {
    background-color: #0c1420;
    border: 1px solid #1c2f44;
    border-radius: 6px;
    padding: 6px 12px;
    color: #c8daea;
    font-size: 12px;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #0f1927;
    border: 1px solid #1c2f44;
    selection-background-color: #0284c7;
    color: #ffffff;
}

/* Table Widget */
QTableWidget {
    background-color: #091018;
    border: 1px solid #172738;
    border-radius: 8px;
    gridline-color: #14202e;
    font-size: 12px;
}
QTableWidget::item {
    padding: 6px;
    border-bottom: 1px solid #111b26;
}
QTableWidget::item:selected {
    background-color: #153b61;
    color: #ffffff;
}
QHeaderView::section {
    background-color: #0d1723;
    color: #8ba3ba;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #1f3750;
    font-weight: bold;
    font-size: 11px;
    text-transform: uppercase;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #080d14;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #1b2e42;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #294563;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Dialogs & MessageBoxes (Arctic Frost Contrast) */
QDialog, QMessageBox, QProgressDialog {
    background-color: #0a121d;
    color: #e2ecf5;
}
QMessageBox QLabel, QProgressDialog QLabel {
    color: #e2ecf5;
    font-size: 13px;
    background-color: transparent;
}
QMessageBox QPushButton, QProgressDialog QPushButton {
    background-color: #131e2c;
    border: 1px solid #22374d;
    color: #ffffff;
    font-size: 12px;
    font-weight: bold;
    border-radius: 6px;
    padding: 6px 18px;
    min-width: 80px;
}
QMessageBox QPushButton:hover, QProgressDialog QPushButton:hover {
    background-color: #1c2d40;
    border-color: #38bdf8;
    color: #ffffff;
}
QMessageBox QPushButton:pressed, QProgressDialog QPushButton:pressed {
    background-color: #101a26;
}

QProgressBar {
    background-color: #0c1420;
    border: 1px solid #1c2f44;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
    border-radius: 5px;
}
"""
