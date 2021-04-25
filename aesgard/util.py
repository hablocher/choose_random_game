# -*- coding: utf-8 -*-
"""
Created on Sat Apr 24 23:18:04 2021

@author: Marcelo
"""
import ctypes
import configparser
import getopt
import os
import sys

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

def writeListToFile(fileName, content):
    with open(fileName, 'w+', encoding="utf-8") as filehandle:  
        for listitem in content:
            filehandle.write('{}\n'.format(listitem))
            
def writeTupleToFile(fileName, _tuple):
    with open(fileName, 'w+', encoding='utf-8') as filehandle:
        for first, second in _tuple:
            filehandle.write("{},{}\n".format(first, second))
    
def readConfigFile(argv):
    config = configparser.ConfigParser()
    myopts, args = getopt.getopt(sys.argv[1:],"i:o:")
    for opt, arg in myopts:
        if opt == '-i':
           if os.path.isfile(arg):
              config.read(arg)
           else:
              config.read("choose_random_game.ini")
        else:
           config.read("choose_random_game.ini")
    return config      
            
