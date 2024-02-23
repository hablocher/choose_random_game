# -*- coding: utf-8 -*-
"""
Created on Thu Feb 22 18:20:06 2024

@author: Marcelo
"""
from PIL import ImageTk

from tkinter import *
from tkinter import messagebox
from aesgard.gameutil import executeGame
from aesgard.gameutil import findSteamGameImage


def showChoosedGame(choosedGame,  steamOwnedGames, config):
    pilImage = findSteamGameImage(steamOwnedGames, config['STEAM']['imageGameURL'], choosedGame)
    root = Tk()
    root.title('Game Choosed')
    #root.geometry('400x400')
        
    # Create a frame
    frame_image = Frame(root, borderwidth=2, bg="white", relief=SUNKEN)
    frame_image.pack(side=TOP, fill="x")

    # Load the image
    my_image = ImageTk.PhotoImage(pilImage)
    image_label = Label(frame_image, image=my_image)
    image_label.pack()
    
    
#   canvas = Canvas(ws, width=199, height=199)
#   canvas.pack()
#   image = ImageTk.PhotoImage(pilImage)
#   image.resize((300, 300), iMAGE.ANTIALIAS)
#   imagesprite = canvas.create_image( 200, 200, image=image)
    Button(root, text=choosedGame, padx=10, pady=5, command=lambda:action(root, choosedGame,  steamOwnedGames, config)).pack(pady=20)
    root.mainloop()    
    
def action(root, choosedGame,  steamOwnedGames, config):
    root.destroy();
    executeGame(choosedGame, steamOwnedGames, config)
