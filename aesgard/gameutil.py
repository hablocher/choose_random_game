# -*- coding: utf-8 -*-
"""
Created on Sat Apr 24 18:56:44 2021

@author: Marcelo
"""
import jellyfish
import os
import sys

from aesgard.steam import playgame

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

def findLaunchAndStart(choosedGame, launcherPrefixes, shortcutExt):
    if os.path.isdir(choosedGame):
        for launch in next(os.walk(choosedGame))[2]:
            for key, prefix in launcherPrefixes:
                if (launch.lower().startswith(prefix.lower()) and launch.lower().endswith(shortcutExt)): 
                   print("Calling '" + launch + "'")
                   os.chdir(choosedGame)
                   os.startfile(launch)
                   sys.exit() 
                   
def findSteamGameAndLaunch(steamGames, choosedGame, playGameURL):
   posLastBar = choosedGame.rfind("/")+1
   for steamGame in steamGames:  
        name = normalizeString(steamGame['name'])
        choosed = normalizeString(choosedGame[posLastBar:])
        if (name == choosed  or jellyfish.levenshtein_distance(name, choosed) == 2):
           print("Calling STEAM app ID " + str(steamGame['appid']) + " (" + steamGame['name'] + ")")
           playgame(playGameURL, steamGame)
           sys.exit() 
                   
def openDOSBOX(choosedGame, DOSBOXShortcut):
    if "DOSBOX" in choosedGame:
        os.startfile(DOSBOXShortcut)
        sys.exit() 

def executeFirstEXE(choosedGame):
    posLastBar = choosedGame.rfind("/")+1
    exeCount = 0
    exeFolder = ""
    exeFile = ""
    for launch in next(os.walk(choosedGame))[2]:
        if launch.lower().endswith('.exe'):
            exeCount += 1
            exeFolder = choosedGame
            exeFile = launch
            if checkExeFile(launch.lower(), choosedGame[posLastBar:].lower()):
                print("Calling EXE '" + launch + "'")
                os.chdir(choosedGame)
                os.startfile(launch)
                sys.exit() 
               
    if (exeCount == 1):
        print("Calling EXE '" + exeFile + "'")
        os.chdir(exeFolder)
        os.startfile(exeFile)
        sys.exit() 
        
def preparelinksList(foldersWithLinks, baseLinks, removals):
    linksList = []
    for key, link in foldersWithLinks:
        if baseLinks:
            linksList = linksList + [s for s in next(os.walk(baseLinks + link))[2]]
        else:
            linksList = linksList + [s for s in next(os.walk(link))[2]]
    
    for key, removal in removals:
        linksList = [g.replace(removal, '') for g in linksList]
    return linksList

def prepareContent(gameFolders, gameCommonFolders, steamGameFolders, linksList):
    content = []
    for key, gameFolder in gameFolders:
        for key, common in gameCommonFolders:
            folder = str(gameFolder) + str(common)
            if os.path.isdir(folder):
                for game in next(os.walk(folder))[1]:
                    if game not in linksList:
                        content = content + [folder + game]
    
    for key, steamFolder in steamGameFolders:
        if os.path.isdir(steamFolder):
            content = content + [steamFolder + "/"+ s for s in next(os.walk(steamFolder))[1]]
    return content
        

