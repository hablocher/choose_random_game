# -*- coding: utf-8 -*-
"""
Created on Thu Feb 22 18:20:06 2024

@author: Marcelo
"""
from PIL import ImageTk

from tkinter import Tk, SUNKEN, TOP, Frame, Label, Button
from aesgard.gameutil import executeGame
from aesgard.gameutil import findGameIcon
from aesgard.config    import Config

def showChoosedGame(choosedGame,  steamOwnedGames):
    conf = Config()
    conf.read_config(None)
    pilImage = findGameIcon(steamOwnedGames, conf.imageURL, choosedGame)
    root = Tk()
    root.title('Game Choosed')
    root.eval('tk::PlaceWindow . center')
    frame_image = Frame(root, borderwidth=2, bg="white", relief=SUNKEN)
    frame_image.pack(side=TOP, fill="x")
    my_image = ImageTk.PhotoImage(pilImage)
    image_label = Label(frame_image, image=my_image)
    image_label.pack()
    Button(root, text="PLAY -> " + choosedGame, padx=10, pady=5, command=lambda:action(root, choosedGame,  steamOwnedGames)).pack(pady=20)
    root.mainloop()    
    
def action(root, choosedGame,  steamOwnedGames):
    root.destroy();
    executeGame(choosedGame, steamOwnedGames)
