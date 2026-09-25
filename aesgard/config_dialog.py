# -*- coding: utf-8 -*-
"""
Unified Settings & Configuration Window for Canino Gaming.
Provides full graphical configuration for:
- Caninos Brancos Theme (Book Editions, Wallpaper, Opacity, SFX)
- Streamer & Live Assistant (YouTube channels, Roulette, OBS Overlay)
- Game Sources & Integrations (Playnite, Steam, eXoDOS, DOSBox)
- Database & Library Maintenance (Sync sources, Clean DB, Backup saves)
"""
import os
import webbrowser
import logging
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QSlider, QSpinBox, QComboBox, QFileDialog,
    QTabWidget, QFrame, QScrollArea, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap, QIcon, QColor

from aesgard.sound import get_sound_manager
from aesgard.backup import backup_game_saves

logger = logging.getLogger(__name__)

CONFIG_DIALOG_STYLESHEET = """
QDialog {
    background-color: #070d14;
    color: #e2ecf5;
    font-family: 'Segoe UI', -apple-system, Arial, sans-serif;
}

QTabWidget::pane {
    border: 1px solid #1c3247;
    background: #09111b;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background: #0d1724;
    color: #8da4b8;
    border: 1px solid #1c3247;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 9px 18px;
    font-size: 12px;
    font-weight: bold;
    margin-right: 4px;
}

QTabBar::tab:hover {
    background: #142234;
    color: #f0f6fc;
}

QTabBar::tab:selected {
    background: #09111b;
    color: #38bdf8;
    border-color: #38bdf8;
    border-bottom: 2px solid #09111b;
}

QGroupBox {
    background: rgba(16, 26, 38, 0.6);
    border: 1px solid #1c3247;
    border-radius: 8px;
    margin-top: 18px;
    padding: 14px 12px 12px 12px;
    font-size: 12px;
    font-weight: bold;
    color: #38bdf8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: #09111b;
}

QLabel {
    color: #cbd5e1;
    font-size: 12px;
}

QLabel.SectionHeader {
    color: #f0f6fc;
    font-size: 13px;
    font-weight: bold;
}

QLineEdit {
    background-color: #0c1420;
    border: 1px solid #1c2f44;
    border-radius: 6px;
    padding: 6px 10px;
    color: #ffffff;
    font-size: 12px;
}
QLineEdit:focus {
    border-color: #38bdf8;
}

QComboBox {
    background-color: #0c1420;
    border: 1px solid #1c2f44;
    border-radius: 6px;
    padding: 6px 10px;
    color: #ffffff;
    font-size: 12px;
}
QComboBox:hover {
    border-color: #38bdf8;
}

QSpinBox {
    background-color: #0c1420;
    border: 1px solid #1c2f44;
    border-radius: 6px;
    padding: 4px 8px;
    color: #ffffff;
    font-size: 12px;
}

QCheckBox {
    color: #e2ecf5;
    font-size: 12px;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #1c3247;
    border-radius: 4px;
    background: #0c1420;
}
QCheckBox::indicator:checked {
    background-color: #0284c7;
    border-color: #38bdf8;
}

QSlider::groove:horizontal {
    border: 1px solid #1c3247;
    height: 6px;
    background: #0c1420;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #ffffff;
    border: 1px solid #38bdf8;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

QPushButton.ActionBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0369a1);
    color: #ffffff;
    font-size: 12px;
    font-weight: bold;
    border: none;
    border-radius: 6px;
    padding: 7px 14px;
}
QPushButton.ActionBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369a1, stop:1 #38bdf8);
}

QPushButton.SecondaryBtn {
    background-color: #121d2a;
    border: 1px solid #1f344a;
    color: #cbd5e1;
    font-size: 12px;
    font-weight: 600;
    border-radius: 6px;
    padding: 6px 12px;
}
QPushButton.SecondaryBtn:hover {
    background-color: #1a2c3f;
    border-color: #38bdf8;
    color: #ffffff;
}

QPushButton.SaveBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
    color: #ffffff;
    font-size: 13px;
    font-weight: bold;
    border: none;
    border-radius: 6px;
    padding: 9px 24px;
}
QPushButton.SaveBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #34d399);
}
"""


class ConfigDialog(QDialog):
    """
    Dedicated unified configuration window for Canino Gaming.
    """
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.dashboard = parent
        self.config = config
        self.setWindowTitle("⚙️ Configurações • Canino Gaming")
        self.resize(760, 600)
        self.setMinimumSize(700, 540)
        self.setStyleSheet(CONFIG_DIALOG_STYLESHEET)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(18, 18, 18, 18)
        self.mainLayout.setSpacing(14)

        # Header Title
        headerBox = QHBoxLayout()
        iconLbl = QLabel("🐺")
        iconLbl.setFont(QFont("Segoe UI", 20))
        titleText = QVBoxLayout()
        titleText.setSpacing(2)
        hTitle = QLabel("CENTRAL DE CONFIGURAÇÕES")
        hTitle.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        hTitle.setStyleSheet("color: #f0f6fc; letter-spacing: 0.8px;")
        hSub = QLabel("Personalize o tema de Caninos Brancos, áudio selvagem, streamer e integrações.")
        hSub.setStyleSheet("color: #7dd3fc; font-size: 11px;")
        titleText.addWidget(hTitle)
        titleText.addWidget(hSub)
        headerBox.addWidget(iconLbl)
        headerBox.addLayout(titleText)
        headerBox.addStretch()
        self.mainLayout.addLayout(headerBox)

        # Tabs Widget
        self.tabs = QTabWidget()
        self.mainLayout.addWidget(self.tabs, 1)

        # Build each tab
        self.buildThemeTab()
        self.buildStreamerTab()
        self.buildSourcesTab()
        self.buildMaintenanceTab()

        # Bottom Buttons (Salvar, Cancelar, Padrões)
        bottomLayout = QHBoxLayout()
        bottomLayout.setSpacing(10)

        self.btnReset = QPushButton("🔄 Restaurar Padrões")
        self.btnReset.setProperty("class", "SecondaryBtn")
        self.btnReset.clicked.connect(self.onResetDefaults)
        bottomLayout.addWidget(self.btnReset)

        bottomLayout.addStretch()

        self.btnCancel = QPushButton("❌ Cancelar")
        self.btnCancel.setProperty("class", "SecondaryBtn")
        self.btnCancel.clicked.connect(self.reject)
        bottomLayout.addWidget(self.btnCancel)

        self.btnSave = QPushButton("💾 Salvar Configurações")
        self.btnSave.setProperty("class", "SaveBtn")
        self.btnSave.clicked.connect(self.onSaveSettings)
        bottomLayout.addWidget(self.btnSave)

        self.mainLayout.addLayout(bottomLayout)

        # Load values into UI
        self.loadCurrentSettings()

    # -------------------------------------------------------------
    # Tab 1: 🐺 Tema & Fundo (Caninos Brancos)
    # -------------------------------------------------------------
    def buildThemeTab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Group 1: Plano de Fundo & Edições de Caninos Brancos
        grpBg = QGroupBox("🖼️ Plano de Fundo & Edições de Caninos Brancos")
        bgLayout = QVBoxLayout(grpBg)
        bgLayout.setSpacing(10)

        # Preset Buttons / Combo
        presetRow = QHBoxLayout()
        presetRow.addWidget(QLabel("Edição Rápida:"))
        self.comboBgPresets = QComboBox()
        self.comboBgPresets.addItems([
            "🐺 Edição L&PM Pocket (Capa Oficial)",
            "🌌 Aurora Boreal do Yukon (Edição Ártica)",
            "📜 Edição Clássica Macmillan 1906 (Trilha da Neve)",
            "⬛ Fundo Escuro Puro (Sem Imagem)",
            "📁 Personalizada (Arquivo do Computador)"
        ])
        self.comboBgPresets.currentIndexChanged.connect(self.onPresetChanged)
        presetRow.addWidget(self.comboBgPresets, 1)
        bgLayout.addLayout(presetRow)

        # Image Path input + browse button + preview
        pathRow = QHBoxLayout()
        pathRow.addWidget(QLabel("Caminho da Imagem:"))
        self.txtBgPath = QLineEdit()
        self.txtBgPath.textChanged.connect(self.updateImagePreview)
        pathRow.addWidget(self.txtBgPath, 1)

        self.btnBrowseBg = QPushButton("📁 Procurar...")
        self.btnBrowseBg.setProperty("class", "SecondaryBtn")
        self.btnBrowseBg.clicked.connect(self.onBrowseBackground)
        pathRow.addWidget(self.btnBrowseBg)
        bgLayout.addLayout(pathRow)

        # Opacity Slider with percentage label & thumbnail
        previewRow = QHBoxLayout()
        previewRow.setSpacing(14)

        # Preview Thumbnail
        self.lblPreviewThumb = QLabel()
        self.lblPreviewThumb.setFixedSize(110, 70)
        self.lblPreviewThumb.setStyleSheet("border: 1px solid #1c3247; border-radius: 6px; background: #070d14;")
        self.lblPreviewThumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        previewRow.addWidget(self.lblPreviewThumb)

        sliderBox = QVBoxLayout()
        sliderBox.setSpacing(4)
        sliderHeader = QHBoxLayout()
        sliderHeader.addWidget(QLabel("Opacidade do Fundo:"))
        self.lblOpacityVal = QLabel("22%")
        self.lblOpacityVal.setStyleSheet("color: #38bdf8; font-weight: bold;")
        sliderHeader.addWidget(self.lblOpacityVal)
        sliderHeader.addStretch()
        sliderBox.addLayout(sliderHeader)

        self.sliderOpacity = QSlider(Qt.Orientation.Horizontal)
        self.sliderOpacity.setRange(0, 60)
        self.sliderOpacity.setValue(22)
        self.sliderOpacity.valueChanged.connect(self.onOpacityChanged)
        sliderBox.addWidget(self.sliderOpacity)

        opHint = QLabel("Dica: 18% a 25% oferece o equilíbrio perfeito entre visibilidade da arte e leitura das cartas.")
        opHint.setStyleSheet("color: #64748b; font-size: 11px;")
        sliderBox.addWidget(opHint)
        previewRow.addLayout(sliderBox, 1)

        bgLayout.addLayout(previewRow)
        layout.addWidget(grpBg)

        # Group 2: Efeitos Sonoros Selvagens & Volume
        grpSfx = QGroupBox("🔊 Efeitos Sonoros Selvagens & Áudio")
        sfxLayout = QVBoxLayout(grpSfx)
        sfxLayout.setSpacing(10)

        self.chkThemeSounds = QCheckBox("🐺 Ativar Sons Temáticos de Caninos Brancos (Uivos de Lobo, Nevasca, Passadas na Neve)")
        sfxLayout.addWidget(self.chkThemeSounds)

        volRow = QHBoxLayout()
        volRow.addWidget(QLabel("Volume dos Efeitos:"))
        self.sliderVolume = QSlider(Qt.Orientation.Horizontal)
        self.sliderVolume.setRange(0, 100)
        self.sliderVolume.setValue(75)
        self.sliderVolume.valueChanged.connect(self.onVolumeChanged)
        volRow.addWidget(self.sliderVolume, 1)

        self.lblVolumeVal = QLabel("75%")
        self.lblVolumeVal.setStyleSheet("color: #38bdf8; font-weight: bold;")
        volRow.addWidget(self.lblVolumeVal)

        self.btnTestSound = QPushButton("🔊 Testar Uivo")
        self.btnTestSound.setProperty("class", "SecondaryBtn")
        self.btnTestSound.clicked.connect(self.onTestSound)
        volRow.addWidget(self.btnTestSound)
        sfxLayout.addLayout(volRow)

        layout.addWidget(grpSfx)
        layout.addStretch()

        self.tabs.addTab(tab, "🐺 Tema & Fundo")

    # -------------------------------------------------------------
    # Tab 2: 📺 Streamer & Live Assistant
    # -------------------------------------------------------------
    def buildStreamerTab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # YouTube Channels Group
        grpYt = QGroupBox("📺 Canais do YouTube")
        ytLayout = QVBoxLayout(grpYt)
        ytLayout.setSpacing(8)

        rowMain = QHBoxLayout()
        rowMain.addWidget(QLabel("Canal Principal (URL):"))
        self.txtYtMain = QLineEdit()
        self.txtYtMain.setPlaceholderText("https://www.youtube.com/@CanalPrincipal")
        rowMain.addWidget(self.txtYtMain, 1)
        ytLayout.addLayout(rowMain)

        rowLive = QHBoxLayout()
        rowLive.addWidget(QLabel("Canal de Lives (URL):"))
        self.txtYtLive = QLineEdit()
        self.txtYtLive.setPlaceholderText("https://www.youtube.com/@CanalLives")
        rowLive.addWidget(self.txtYtLive, 1)
        ytLayout.addLayout(rowLive)

        layout.addWidget(grpYt)

        # Roulette & Animation Group
        grpRoulette = QGroupBox("🎲 Roleta do Sorteador & Sorteios ao Vivo")
        rLayout = QVBoxLayout(grpRoulette)
        rLayout.setSpacing(8)

        self.chkRouletteEnabled = QCheckBox("Ativar animação de Roleta ao sortear novos jogos")
        rLayout.addWidget(self.chkRouletteEnabled)

        durRow = QHBoxLayout()
        durRow.addWidget(QLabel("Duração da Roleta:"))
        self.spinRouletteDur = QSpinBox()
        self.spinRouletteDur.setRange(800, 8000)
        self.spinRouletteDur.setSingleStep(200)
        self.spinRouletteDur.setSuffix(" ms")
        durRow.addWidget(self.spinRouletteDur)
        durRow.addWidget(QLabel("(Ex: 2600 ms = 2.6 segundos)"))
        durRow.addStretch()
        rLayout.addLayout(durRow)

        layout.addWidget(grpRoulette)

        # Web Overlay for OBS Studio
        grpObs = QGroupBox("📡 Overlay HTML5 para OBS Studio")
        obsLayout = QVBoxLayout(grpObs)
        obsLayout.setSpacing(8)

        obsInfo = QLabel("O Canino Gaming roda um servidor local transparente em <b>http://localhost:8089/overlay</b> para capturar no OBS como Navegador.")
        obsInfo.setWordWrap(True)
        obsLayout.addWidget(obsInfo)

        chromaRow = QHBoxLayout()
        chromaRow.addWidget(QLabel("Chroma Key Padrão:"))
        self.comboChroma = QComboBox()
        self.comboChroma.addItems(["dark (Transparência Escura)", "green (Verde #00FF00)", "magenta (Magenta #FF00FF)", "transparent (Transparente)"])
        chromaRow.addWidget(self.comboChroma, 1)

        self.btnOpenOverlay = QPushButton("🌐 Abrir Overlay no Navegador")
        self.btnOpenOverlay.setProperty("class", "ActionBtn")
        self.btnOpenOverlay.clicked.connect(lambda: webbrowser.open("http://localhost:8089/overlay"))
        chromaRow.addWidget(self.btnOpenOverlay)
        obsLayout.addLayout(chromaRow)

        layout.addWidget(grpObs)
        layout.addStretch()

        self.tabs.addTab(tab, "📺 Streamer & Live")

    # -------------------------------------------------------------
    # Tab 3: 🎮 Fontes de Jogos & Integrações
    # -------------------------------------------------------------
    def buildSourcesTab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Playnite Group
        grpPlaynite = QGroupBox("⚡ Integração Playnite (Steam, GOG, Epic, Emuladores)")
        pnLayout = QVBoxLayout(grpPlaynite)
        pnLayout.setSpacing(8)

        self.chkPlayniteEnabled = QCheckBox("Ativar integração com biblioteca do Playnite")
        pnLayout.addWidget(self.chkPlayniteEnabled)

        pnRow = QHBoxLayout()
        pnRow.addWidget(QLabel("Pasta do Playnite:"))
        self.txtPlaynitePath = QLineEdit()
        pnRow.addWidget(self.txtPlaynitePath, 1)
        self.btnBrowsePlaynite = QPushButton("📁 Procurar...")
        self.btnBrowsePlaynite.setProperty("class", "SecondaryBtn")
        self.btnBrowsePlaynite.clicked.connect(self.onBrowsePlaynite)
        pnRow.addWidget(self.btnBrowsePlaynite)
        pnLayout.addLayout(pnRow)

        self.chkPlayniteOnlyInstalled = QCheckBox("Importar apenas jogos atualmente marcados como instalados no Playnite")
        pnLayout.addWidget(self.chkPlayniteOnlyInstalled)

        btnExportRow = QHBoxLayout()
        self.btnRunExport = QPushButton("⚡ Re-exportar Biblioteca do Playnite Agora")
        self.btnRunExport.setProperty("class", "ActionBtn")
        self.btnRunExport.clicked.connect(self.onExportPlayniteTriggered)
        btnExportRow.addWidget(self.btnRunExport)
        btnExportRow.addStretch()
        pnLayout.addLayout(btnExportRow)

        layout.addWidget(grpPlaynite)

        # Steam Group
        grpSteam = QGroupBox("💨 Integração Steam")
        steamLayout = QVBoxLayout(grpSteam)
        steamLayout.setSpacing(8)

        self.chkSteamEnabled = QCheckBox("Ativar integração direta com Steam")
        steamLayout.addWidget(self.chkSteamEnabled)

        steamRow = QHBoxLayout()
        steamRow.addWidget(QLabel("Pasta do Steam:"))
        self.txtSteamPath = QLineEdit()
        steamRow.addWidget(self.txtSteamPath, 1)
        self.btnBrowseSteam = QPushButton("📁 Procurar...")
        self.btnBrowseSteam.setProperty("class", "SecondaryBtn")
        self.btnBrowseSteam.clicked.connect(self.onBrowseSteam)
        steamRow.addWidget(self.btnBrowseSteam)
        steamLayout.addLayout(steamRow)

        layout.addWidget(grpSteam)

        # Retro / eXoDOS Group
        grpRetro = QGroupBox("📜 eXoDOS & Clássicos MS-DOS")
        retroLayout = QVBoxLayout(grpRetro)
        retroLayout.setSpacing(8)

        exoRow = QHBoxLayout()
        exoRow.addWidget(QLabel("Pasta do eXoDOS:"))
        self.txtExodosPath = QLineEdit()
        exoRow.addWidget(self.txtExodosPath, 1)
        self.btnBrowseExodos = QPushButton("📁 Procurar...")
        self.btnBrowseExodos.setProperty("class", "SecondaryBtn")
        self.btnBrowseExodos.clicked.connect(self.onBrowseExodos)
        exoRow.addWidget(self.btnBrowseExodos)
        retroLayout.addLayout(exoRow)

        layout.addWidget(grpRetro)
        layout.addStretch()

        self.tabs.addTab(tab, "🎮 Fontes & Integrações")

    # -------------------------------------------------------------
    # Tab 4: 🛠️ Manutenção & Banco
    # -------------------------------------------------------------
    def buildMaintenanceTab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # General Library Options
        grpGeneral = QGroupBox("🎲 Parâmetros de Sorteio & Capas")
        genLayout = QVBoxLayout(grpGeneral)
        genLayout.setSpacing(8)

        sampleRow = QHBoxLayout()
        sampleRow.addWidget(QLabel("Tamanho da Amostra Randômica (Sample Size):"))
        self.spinSampleSize = QSpinBox()
        self.spinSampleSize.setRange(5, 200)
        self.spinSampleSize.setValue(25)
        sampleRow.addWidget(self.spinSampleSize)
        sampleRow.addWidget(QLabel("jogos (Garante variedade estocástica a cada sorteio)"))
        sampleRow.addStretch()
        genLayout.addLayout(sampleRow)

        self.chkFetchCovers = QCheckBox("Buscar capas online automaticamente (Steam / IGDB) quando indisponíveis localmente")
        genLayout.addWidget(self.chkFetchCovers)

        layout.addWidget(grpGeneral)

        # Maintenance Actions
        grpActions = QGroupBox("🛠️ Operações de Banco de Dados")
        actLayout = QVBoxLayout(grpActions)
        actLayout.setSpacing(12)

        syncRow = QHBoxLayout()
        self.btnDoSync = QPushButton("🔄 Sincronizar Todas as Fontes")
        self.btnDoSync.setProperty("class", "ActionBtn")
        self.btnDoSync.clicked.connect(self.onTriggerSyncSources)
        syncRow.addWidget(self.btnDoSync)
        syncLbl = QLabel("Re-escaneia Playnite, atalhos do desktop e pastas locais para cadastrar novos jogos.")
        syncLbl.setWordWrap(True)
        syncRow.addWidget(syncLbl, 1)
        actLayout.addLayout(syncRow)

        cleanRow = QHBoxLayout()
        self.btnDoClean = QPushButton("🧹 Limpar Banco de Dados")
        self.btnDoClean.setProperty("class", "ActionBtn")
        self.btnDoClean.clicked.connect(self.onTriggerCleanDb)
        cleanRow.addWidget(self.btnDoClean)
        cleanLbl = QLabel("Verifica jogos não mais instalados e os atualiza sem apagar histórico ou favoritos.")
        cleanLbl.setWordWrap(True)
        cleanRow.addWidget(cleanLbl, 1)
        actLayout.addLayout(cleanRow)

        backupRow = QHBoxLayout()
        self.btnDoBackup = QPushButton("💾 Fazer Backup de Saves & Banco")
        self.btnDoBackup.setProperty("class", "ActionBtn")
        self.btnDoBackup.clicked.connect(self.onTriggerBackup)
        backupRow.addWidget(self.btnDoBackup)
        backupLbl = QLabel("Cria um backup compactado de segurança com o banco de dados e arquivos locais.")
        backupLbl.setWordWrap(True)
        backupRow.addWidget(backupLbl, 1)
        actLayout.addLayout(backupRow)

        layout.addWidget(grpActions)
        layout.addStretch()

        self.tabs.addTab(tab, "🛠️ Manutenção & Banco")

    # -------------------------------------------------------------
    # Logic: Load & Save
    # -------------------------------------------------------------
    def loadCurrentSettings(self):
        cfg = self.config
        if not cfg:
            return

        # 1. Theme
        bg_path = getattr(cfg, 'themeBackgroundImage', 'assets/backgrounds/caninos_brancos_lpm.png')
        self.txtBgPath.setText(bg_path)
        self.syncPresetCombo(bg_path)

        opacity = int(getattr(cfg, 'themeBackgroundOpacity', 0.22) * 100)
        self.sliderOpacity.setValue(max(0, min(60, opacity)))
        self.lblOpacityVal.setText(f"{opacity}%")

        sm = get_sound_manager()
        self.chkThemeSounds.setChecked(getattr(cfg, 'themeSounds', True))
        vol = int(sm.get_volume() * 100)
        self.sliderVolume.setValue(vol)
        self.lblVolumeVal.setText(f"{vol}%")

        # 2. Streamer
        self.txtYtMain.setText(getattr(cfg, 'streamerYouTubeMainChannel', ''))
        self.txtYtLive.setText(getattr(cfg, 'streamerYouTubeLiveChannel', ''))
        self.chkRouletteEnabled.setChecked(getattr(cfg, 'streamerRouletteEnabled', True))
        self.spinRouletteDur.setValue(getattr(cfg, 'streamerRouletteDurationMs', 2600))
        
        chroma = getattr(cfg, 'streamerOverlayChromaKey', 'dark')
        idx = self.comboChroma.findText(chroma, Qt.MatchFlag.MatchContains)
        if idx >= 0:
            self.comboChroma.setCurrentIndex(idx)

        # 3. Sources
        self.chkPlayniteEnabled.setChecked(getattr(cfg, 'playniteEnabled', True))
        self.txtPlaynitePath.setText(getattr(cfg, 'playnitePath', ''))
        self.chkPlayniteOnlyInstalled.setChecked(getattr(cfg, 'playniteOnlyInstalled', False))

        self.chkSteamEnabled.setChecked(getattr(cfg, 'steamEnabled', True))
        self.txtSteamPath.setText(getattr(cfg, 'steamPath', ''))

        self.txtExodosPath.setText(getattr(cfg, 'EXODOSLocation', ''))

        # 4. Maintenance
        self.spinSampleSize.setValue(getattr(cfg, 'randomSampleSize', 25))
        self.chkFetchCovers.setChecked(getattr(cfg, 'fetchOnlineCovers', True))

        self.updateImagePreview(bg_path)

    def onSaveSettings(self):
        """Persists all configuration to choose_random_game.ini and applies live updates."""
        settings = {
            "THEME": {
                "backgroundImage": self.txtBgPath.text().strip(),
                "backgroundOpacity": f"{(self.sliderOpacity.value() / 100.0):.2f}",
                "themeSounds": str(self.chkThemeSounds.isChecked())
            },
            "STREAMER": {
                "youtubeMainChannel": self.txtYtMain.text().strip(),
                "youtubeLiveChannel": self.txtYtLive.text().strip(),
                "rouletteEnabled": str(self.chkRouletteEnabled.isChecked()),
                "rouletteDurationMs": str(self.spinRouletteDur.value()),
                "overlayChromaKey": self.comboChroma.currentText().split()[0]
            },
            "PLAYNITE": {
                "enabled": str(self.chkPlayniteEnabled.isChecked()),
                "path": self.txtPlaynitePath.text().strip(),
                "onlyInstalled": str(self.chkPlayniteOnlyInstalled.isChecked())
            },
            "STEAM": {
                "enabled": str(self.chkSteamEnabled.isChecked()),
                "steamPath": self.txtSteamPath.text().strip()
            },
            "EXODOS": {
                "EXODOSLocation": self.txtExodosPath.text().strip()
            },
            "CONFIG": {
                "randomSampleSize": str(self.spinSampleSize.value()),
                "fetchOnlineCovers": str(self.chkFetchCovers.isChecked())
            }
        }

        success = self.config.save_all_settings(settings)
        if success:
            # Apply to sound manager
            sm = get_sound_manager()
            sm.set_theme_mode(self.chkThemeSounds.isChecked())
            sm.set_volume(self.sliderVolume.value() / 100.0)

            # Apply background immediately to parent dashboard
            if self.dashboard and hasattr(self.dashboard, 'setBackgroundPreset'):
                new_bg = self.txtBgPath.text().strip()
                new_op = self.sliderOpacity.value() / 100.0
                self.dashboard.setBackgroundPreset(new_bg, new_op)

            # Audio confirmation
            sm.play("snow_crunch")
            QMessageBox.information(self, "Sucesso", "Configurações salvas com sucesso no choose_random_game.ini!")
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível gravar no arquivo choose_random_game.ini.")

    def onResetDefaults(self):
        confirm = QMessageBox.question(
            self,
            "Restaurar Padrões",
            "Deseja restaurar as configurações padrão recomendadas de Caninos Brancos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.txtBgPath.setText("assets/backgrounds/caninos_brancos_lpm.png")
            self.comboBgPresets.setCurrentIndex(0)
            self.sliderOpacity.setValue(22)
            self.chkThemeSounds.setChecked(True)
            self.sliderVolume.setValue(75)
            self.chkRouletteEnabled.setChecked(True)
            self.spinRouletteDur.setValue(2600)
            self.spinSampleSize.setValue(25)
            self.chkFetchCovers.setChecked(True)

    # -------------------------------------------------------------
    # Helper Handlers
    # -------------------------------------------------------------
    def onPresetChanged(self, idx):
        presets = [
            ("assets/backgrounds/caninos_brancos_lpm.png", 22),
            ("assets/backgrounds/white_fang_boreal_aurora.jpg", 20),
            ("assets/backgrounds/white_fang_classic_1906.jpg", 18),
            ("", 0),
            (None, None)
        ]
        if idx < len(presets) and presets[idx][0] is not None:
            path, op = presets[idx]
            self.txtBgPath.setText(path)
            self.sliderOpacity.setValue(op)

    def syncPresetCombo(self, path):
        norm = path.replace("\\", "/").strip()
        if "caninos_brancos_lpm" in norm:
            self.comboBgPresets.setCurrentIndex(0)
        elif "white_fang_boreal_aurora" in norm:
            self.comboBgPresets.setCurrentIndex(1)
        elif "white_fang_classic_1906" in norm:
            self.comboBgPresets.setCurrentIndex(2)
        elif not norm:
            self.comboBgPresets.setCurrentIndex(3)
        else:
            self.comboBgPresets.setCurrentIndex(4)

    def updateImagePreview(self, path):
        path = path.strip()
        if path and os.path.exists(path):
            pix = QPixmap(path)
            if not pix.isNull():
                self.lblPreviewThumb.setPixmap(pix.scaled(110, 70, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
                return
        self.lblPreviewThumb.setText("Sem Fundo")
        self.lblPreviewThumb.setPixmap(QPixmap())

    def onOpacityChanged(self, val):
        self.lblOpacityVal.setText(f"{val}%")

    def onVolumeChanged(self, val):
        self.lblVolumeVal.setText(f"{val}%")
        get_sound_manager().set_volume(val / 100.0)

    def onTestSound(self):
        sm = get_sound_manager()
        sm.set_volume(self.sliderVolume.value() / 100.0)
        sm.play("wolf_howl")

    def onBrowseBackground(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Imagem de Fundo",
            "",
            "Imagens (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if file_path:
            self.txtBgPath.setText(file_path)
            self.comboBgPresets.setCurrentIndex(4)

    def onBrowsePlaynite(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Instalação do Playnite")
        if folder:
            self.txtPlaynitePath.setText(folder)

    def onBrowseSteam(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta do Steam")
        if folder:
            self.txtSteamPath.setText(folder)

    def onBrowseExodos(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta do eXoDOS")
        if folder:
            self.txtExodosPath.setText(folder)

    def onExportPlayniteTriggered(self):
        if self.dashboard and hasattr(self.dashboard, 'onExportPlaynite'):
            self.dashboard.onExportPlaynite()

    def onTriggerSyncSources(self):
        if self.dashboard and hasattr(self.dashboard, 'onSyncSources'):
            self.dashboard.onSyncSources()

    def onTriggerCleanDb(self):
        if self.dashboard and hasattr(self.dashboard, 'onCleanDatabase'):
            self.dashboard.onCleanDatabase()

    def onTriggerBackup(self):
        res = backup_game_saves()
        if res.get("success"):
            QMessageBox.information(self, "Backup Concluído", f"Backup de segurança gerado com sucesso em:\n{res.get('archive_path')}")
        else:
            QMessageBox.warning(self, "Aviso", f"Não foi possível concluir o backup: {res.get('error')}")
