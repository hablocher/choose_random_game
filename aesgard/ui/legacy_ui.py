# -*- coding: utf-8 -*-
"""
Legacy Tkinter UI for Choose Random Game.
"""
import os
import logging
from PIL import ImageTk, Image
from tkinter import Tk, SUNKEN, TOP, Frame, Label, Button, StringVar, messagebox

from aesgard.gameutil import executeGame, findGameIcon, chooseGame
from aesgard.database import setFinished, setFavorite, findGameInfo
from aesgard.config import Config
from aesgard.ui.formatting import formatDisplayName

logger = logging.getLogger(__name__)


class GameChooserUI:
    def __init__(self, content, currentChoice, steamOwnedGames, config):
        self.content = content
        self.currentChoice = currentChoice
        self.steamOwnedGames = steamOwnedGames
        self.config = config
        
        self.root = Tk()
        self.root.title("Canino Gaming")
        self.root.resizable(False, False)
        self.root.configure(bg="#070d14")

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
        self.frameImage = Frame(self.root, bg="#0f1b2b", relief=SUNKEN, bd=2)
        self.frameImage.pack(side=TOP, pady=(15, 10))

        self.imageLabel = Label(self.frameImage, bg="#0f1b2b")
        self.imageLabel.pack()

        self.titleLabel = Label(
            self.root, 
            textvariable=self.titleVar, 
            font=("Segoe UI", 12, "bold"), 
            bg="#070d14", 
            fg="#f0f6fc",
            wraplength=380,
            justify="center"
        )
        self.titleLabel.pack(pady=(0, 5))

        self.statsLabel = Label(
            self.root,
            textvariable=self.statsVar,
            font=("Segoe UI", 9),
            bg="#070d14", 
            fg="#7dd3fc"
        )
        self.statsLabel.pack(pady=(0, 10))

        btnFrame = Frame(self.root, bg="#070d14")
        btnFrame.pack(pady=5)

        self.btnPlay = Button(
            btnFrame, 
            text="▶ CAÇAR (JOGAR)", 
            font=("Segoe UI", 10, "bold"), 
            bg="#0284c7", 
            fg="white", 
            activebackground="#0369a1", 
            activeforeground="white",
            relief="flat",
            padx=15, 
            pady=6, 
            command=self.onPlay
        )
        self.btnPlay.grid(row=0, column=0, padx=6)

        self.btnReroll = Button(
            btnFrame, 
            text="🎲 Nova Presa", 
            font=("Segoe UI", 10), 
            bg="#1e3a8a", 
            fg="white", 
            activebackground="#2563eb", 
            activeforeground="white",
            relief="flat",
            padx=12, 
            pady=6, 
            command=self.onReroll
        )
        self.btnReroll.grid(row=0, column=1, padx=6)

        actionFrame = Frame(self.root, bg="#070d14")
        actionFrame.pack(pady=8)

        self.btnFav = Button(
            actionFrame,
            text="⭐ Favoritar",
            font=("Segoe UI", 8),
            bg="#121d2a",
            fg="#c8daea",
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
            bg="#121d2a",
            fg="#c8daea",
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

        info = findGameInfo(gameEntry)
        times_played = info[2] if info else 0
        self.statsVar.set(f"Jogado: {times_played}x")

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
