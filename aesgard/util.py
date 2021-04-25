# -*- coding: utf-8 -*-
"""
Created on Sat Apr 24 23:18:04 2021

@author: Marcelo
"""
import ctypes

##  Styles:
##  0 : OK
##  1 : OK | Cancel
##  2 : Abort | Retry | Ignore
##  3 : Yes | No | Cancel
##  4 : Yes | No
##  5 : Retry | No 
##  6 : Cancel | Try Again | Continue
def Mbox(title, text, style):
    ctypes.windll.user32.MessageBoxW(0, text, title, style)
    
#Mbox(str(len(content)) + ' jogos!!!! JOGUE UM ',  game , 0)