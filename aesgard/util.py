# -*- coding: utf-8 -*-
"""
Created on Sat Apr 24 18:56:44 2021

@author: Marcelo
"""

import ctypes
import jellyfish

def normalizeString(text):
    return text.replace(" ","").replace(":","").replace("-","").replace("'","").replace(",","").replace("!","").replace("+","").replace("(","").replace(")","").lower()

def checkExeFile(launch, choosed):
    if jellyfish.levenshtein_distance(launch,  choosed) == 2: 
        return True
    if 'launcher.exe' in launch.lower():
        return True
    if not "unins" in launch.lower(): 
        return True
    return False    

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