# -*- coding: utf-8 -*-
"""
User Interface module for Choose Random Game using Tkinter.
Features:
- Image/cover preview
- Play button
- Reroll / Sortear Outro button (instant redraw without closing)
- Quick toggle for Finished / Favorite status
"""
import os
import logging
from PIL import ImageTk, Image

from tkinter import Tk, SUNKEN, TOP, Frame, Label, Button, StringVar, messagebox
from aesgard.gameutil import executeGame, findGameIcon, chooseGame
from aesgard.database import setFinished, setFavorite, findGameInfo
from aesgard.config import Config

logger = logging.getLogger(__name__)

def formatDisplayName(rawName):
    """Generates a clean, human-readable display title from raw game entry."""
    if not rawName:
        return ""
    name = str(rawName)
    if name.startswith("playnite:"):
        parts = name.split(":")
        if len(parts) >= 2:
            return parts[1]
    elif name.startswith("steam:"):
        parts = name.split(":")
        if len(parts) >= 2:
            return parts[1]
    elif name.startswith("exodos:"):
        path = name[len("exodos:"):]
        # Try to extract the title from the .bat file inside the game folder
        try:
            from aesgard.gameutil import geteXoDOSGameDetails
            _, title = geteXoDOSGameDetails(path)
            return f"[eXoDOS] {title}"
        except Exception:
            return f"[eXoDOS] {os.path.basename(path.rstrip('/\\'))}"
    elif name.startswith("link::"):
        clean = name[len("link::"):]
        basename = os.path.basename(clean)
        return os.path.splitext(basename)[0]
    elif name.startswith("gog:"):
        return f"[GOG] {name[4:]}"
    else:
        # Local folder path
        clean = name.replace("\\", "/").rstrip("/")
        folder_title = clean.split("/")[-1]
        if "dosbox" in clean.lower():
            return f"[DOSBox] {folder_title}"
        return folder_title
    return name

class GameChooserUI:
    def __init__(self, content, currentChoice, steamOwnedGames, config):
        self.content = content
        self.currentChoice = currentChoice
        self.steamOwnedGames = steamOwnedGames
        self.config = config
        
        self.root = Tk()
        self.root.title("Choose Random Game")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e24")

        # Variables
        self.titleVar = StringVar()
        self.statsVar = StringVar()
        self.photoImage = None

        # Build Layout
        self.createWidgets()
        self.updateGameDisplay(self.currentChoice)

        # Center Window
        self.root.update_idletasks()
        w = 420
        h = 380
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def createWidgets(self):
        # Image Frame
        self.frameImage = Frame(self.root, bg="#2d3436", relief=SUNKEN, bd=2)
        self.frameImage.pack(side=TOP, pady=(15, 10))

        self.imageLabel = Label(self.frameImage, bg="#2d3436")
        self.imageLabel.pack()

        # Title
        self.titleLabel = Label(
            self.root, 
            textvariable=self.titleVar, 
            font=("Segoe UI", 12, "bold"), 
            bg="#1e1e24", 
            fg="#f5f6fa",
            wraplength=380,
            justify="center"
        )
        self.titleLabel.pack(pady=(0, 5))

        # Stats / Info
        self.statsLabel = Label(
            self.root,
            textvariable=self.statsVar,
            font=("Segoe UI", 9),
            bg="#1e1e24",
            fg="#a4b0be"
        )
        self.statsLabel.pack(pady=(0, 10))

        # Buttons Frame
        btnFrame = Frame(self.root, bg="#1e1e24")
        btnFrame.pack(pady=5)

        # PLAY Button
        self.btnPlay = Button(
            btnFrame, 
            text="▶ JOGAR", 
            font=("Segoe UI", 10, "bold"), 
            bg="#00b894", 
            fg="white", 
            activebackground="#00a885", 
            activeforeground="white",
            relief="flat",
            padx=15, 
            pady=6, 
            command=self.onPlay
        )
        self.btnPlay.grid(row=0, column=0, padx=6)

        # REROLL Button
        self.btnReroll = Button(
            btnFrame, 
            text="🎲 Sortear Outro", 
            font=("Segoe UI", 10), 
            bg="#0984e3", 
            fg="white", 
            activebackground="#0874c7", 
            activeforeground="white",
            relief="flat",
            padx=12, 
            pady=6, 
            command=self.onReroll
        )
        self.btnReroll.grid(row=0, column=1, padx=6)

        # Action Buttons (Favorite / Finish)
        actionFrame = Frame(self.root, bg="#1e1e24")
        actionFrame.pack(pady=8)

        self.btnFav = Button(
            actionFrame,
            text="⭐ Favoritar",
            font=("Segoe UI", 8),
            bg="#2d3436",
            fg="#f5f6fa",
            relief="flat",
            padx=8,
            pady=3,
            command=self.onToggleFavorite
        )
        self.btnFav.grid(row=0, column=0, padx=5)

        self.btnFinish = Button(
            actionFrame,
            text="✔ Marcar como Zerado",
            font=("Segoe UI", 8),
            bg="#2d3436",
            fg="#f5f6fa",
            relief="flat",
            padx=8,
            pady=3,
            command=self.onToggleFinished
        )
        self.btnFinish.grid(row=0, column=1, padx=5)

    def updateGameDisplay(self, gameEntry):
        self.currentChoice = gameEntry
        cleanTitle = formatDisplayName(gameEntry)
        self.titleVar.set(cleanTitle)

        # Update stats
        info = findGameInfo(gameEntry)
        times_played = info[2] if info else 0
        self.statsVar.set(f"Jogado: {times_played}x")

        # Load Icon
        try:
            pilImg = findGameIcon(
                gameEntry, 
                playnitePath=getattr(self.config, 'playnitePath', '')
            )
        except Exception as e:
            logger.warning(f"Error loading icon: {e}")
            pilImg = Image.new("RGB", (128, 128), (45, 52, 54))

        self.photoImage = ImageTk.PhotoImage(pilImg)
        self.imageLabel.configure(image=self.photoImage)

    def onPlay(self):
        choice = self.currentChoice
        self.root.destroy()
        logger.info(f"Starting game: {choice}")
        executeGame(choice, self.steamOwnedGames)

    def onReroll(self):
        newChoice = chooseGame(self.content)
        if newChoice:
            self.updateGameDisplay(newChoice)

    def onToggleFavorite(self):
        setFavorite(self.currentChoice, 1)
        messagebox.showinfo("Favorito", f"'{formatDisplayName(self.currentChoice)}' foi adicionado aos favoritos!")

    def onToggleFinished(self):
        setFinished(self.currentChoice, 1)
        messagebox.showinfo("Zerado", f"'{formatDisplayName(self.currentChoice)}' marcado como concluído/zerado!")

    def start(self):
        self.root.mainloop()

def showChoosedGame(choosedGame, steamOwnedGames, content=None):
    conf = Config()
    conf.read_config(None)
    contentList = content or [choosedGame]
    app = GameChooserUI(contentList, choosedGame, steamOwnedGames, conf)
    app.start()

_PLAYNITE_META_CACHE = None

def clearPlayniteMetaCache():
    """Clears cached Playnite metadata to force reload from playnite_games.json."""
    global _PLAYNITE_META_CACHE
    _PLAYNITE_META_CACHE = None

def _getPlayniteMetaCache():
    global _PLAYNITE_META_CACHE
    if _PLAYNITE_META_CACHE is None:
        _PLAYNITE_META_CACHE = {}
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(project_dir, "playnite_games.json")
        if os.path.exists(json_path):
            try:
                import json
                with open(json_path, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                    for item in data:
                        gid = item.get("Id") or item.get("id")
                        if gid:
                            _PLAYNITE_META_CACHE[gid] = {
                                "platform": item.get("Platform") or "",
                                "source": item.get("Source") or "Playnite"
                            }
            except Exception:
                pass
    return _PLAYNITE_META_CACHE

def detectPlatform(rawName: str) -> str:
    """Detects the platform/source of a game entry with emulator and store awareness."""
    name_str = str(rawName)
    if name_str.startswith("playnite:"):
        parts = name_str.split(":")
        if len(parts) >= 3:
            game_id = parts[-1]
            cache = _getPlayniteMetaCache()
            if game_id in cache:
                meta = cache[game_id]
                plat = meta.get("platform", "")
                src = meta.get("source", "")
                # If it's a console/emulator platform, show the console platform!
                if plat and "PC" not in plat:
                    return plat
                # If it's a known store source, show the store!
                if src and src != "Playnite":
                    return src
                if plat:
                    return plat
        return "Playnite"
    elif name_str.startswith("steam:"):
        return "Steam"
    elif name_str.startswith("exodos:") or "exodos" in name_str.lower():
        return "eXoDOS"
    elif name_str.startswith("link::"):
        return "Atalho / Desktop"
    elif "dosbox" in name_str.lower():
        return "DOSBox"
    elif name_str.startswith("gog:"):
        return "GOG"
    else:
        return "Instalação Local"

def getPlatformColor(platform: str) -> str:
    """Returns a distinct badge color for each platform/console/store."""
    plat_lower = platform.lower()
    
    # Consoles & Emulators
    if "nintendo 64" in plat_lower or "n64" in plat_lower:
        return "#c0392b"
    if "snes" in plat_lower:
        return "#8e44ad"
    if "playstation 2" in plat_lower or "ps2" in plat_lower:
        return "#1e3799"
    if "playstation" in plat_lower or "ps1" in plat_lower:
        return "#2980b9"
    if "game boy" in plat_lower or "gba" in plat_lower:
        return "#5f27cd"
    if "gamecube" in plat_lower:
        return "#4834d4"
    if "switch" in plat_lower:
        return "#eb4d4b"
    if "sega" in plat_lower or "genesis" in plat_lower or "dreamcast" in plat_lower:
        return "#0984e3"
    if "nintendo" in plat_lower:
        return "#d63031"

    # Stores & Sources
    colors = {
        "Steam": "#1b2838",
        "eXoDOS": "#744210",
        "Playnite": "#ff6b6b",
        "Atalho / Desktop": "#2c3e50",
        "DOSBox": "#4a5568",
        "GOG": "#4b1e78",
        "Epic": "#2d3436",
        "Epic Games": "#2d3436",
        "Xbox": "#107c10",
        "Amazon": "#e67e22",
        "Amazon Games": "#e67e22",
        "Ubisoft": "#0984e3",
        "Ubisoft Connect": "#0984e3",
        "EA app": "#ff4757",
        "Battle.net": "#00a8ff",
        "Riot Games": "#eb4d4b",
        "Legacy Games": "#2c3e50",
        "Instalação Local": "#1a365d"
    }
    return colors.get(platform, "#2d3748")
