# -*- coding: utf-8 -*-
"""
Created on Sat Apr 24 18:56:44 2021

@author: Marcelo
"""
import jellyfish
import os
import sys

from aesgard.steam import playgame
from aesgard.steam import playgameid

def normalizeString(text):
    return text.replace(" ","").replace(":","").replace("-","").replace("'","").replace(",","").replace("!","").replace("+","").replace("(","").replace(")","").lower()

def checkExeFile(launch, choosed):
    if jellyfish.levenshtein_distance(launch, choosed) == 2: 
        return True
    if 'launcher.exe' == launch:
        return True
    return False    

def findLauncherAndStart(launcherPrefixes, shortcutExt):
    if os.path.isdir(__CHOOSEDGAME__):
        for launch in next(os.walk(__CHOOSEDGAME__))[2]:
            for key, prefix in launcherPrefixes:
                if (launch.lower().startswith(prefix.lower()) and launch.lower().endswith(shortcutExt)): 
                   print("Calling '" + launch + "'")
                   os.chdir(__CHOOSEDGAME__)
                   os.startfile(launch)
                   sys.exit(0) 
                   
def findSteamGameAndLaunch(steamGames, playGameURL, chooseNotInstalled):
   if not chooseNotInstalled:
       posLastBar = __CHOOSEDGAME__.rfind("/")+1
       for steamGame in steamGames:  
            name = normalizeString(steamGame['name'])
            choosed = normalizeString(__CHOOSEDGAME__[posLastBar:])
            if (name == choosed  or jellyfish.levenshtein_distance(name, choosed) == 2):
               print("Calling STEAM app ID " + str(steamGame['appid']) + " (" + steamGame['name'] + ")")
               playgame(playGameURL, steamGame)
               sys.exit(0) 
   else:
       if __CHOOSEDGAME__.startswith("steam:"):
           pos = __CHOOSEDGAME__.rfind(":") + 1
           print("Calling STEAM app ID " + __CHOOSEDGAME__)
           print(__CHOOSEDGAME__[pos:])
           playgameid(playGameURL, __CHOOSEDGAME__[pos:])
           sys.exit(0) 
                   
def openDOSBOX(DOSBOXShortcut):
    if "DOSBOX" in __CHOOSEDGAME__:
        os.startfile(DOSBOXShortcut)
        sys.exit(0) 

def executeEXE():
    """
    Execute EXE if the folder contains ONLY one EXE or
    the EXE name is similar (levenshtein distance) to game name

    Returns
    -------
    None.

    """
    posLastBar = __CHOOSEDGAME__.rfind("/")
    exeCount = 0
    exeFolder = ""
    exeFile = ""
    for launch in next(os.walk(__CHOOSEDGAME__))[2]:
        if launch.lower().endswith('.exe'):
            exeCount += 1
            exeFolder = __CHOOSEDGAME__
            exeFile = launch
            if checkExeFile(launch.lower(), __CHOOSEDGAME__[posLastBar:].lower()):
                print("Calling EXE '" + launch + "'")
                os.chdir(__CHOOSEDGAME__)
                os.startfile(launch)
                sys.exit(0) 
               
    if (exeCount == 1):
        print("Calling EXE '" + exeFile + "'")
        os.chdir(exeFolder)
        os.startfile(exeFile)
        sys.exit(0) 

def fallBackToGameFolder():
    # Fallback and open the game folder
    print("Opening folder '" + __CHOOSEDGAME__ + "'")
    os.startfile(__CHOOSEDGAME__)
    sys.exit(0)
        
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

def prepareContent(gameFolders, gameCommonFolders, steamGameFolders, linksList, steamOwnedGames, chooseNotInstalled):
    content = []
    for key, gameFolder in gameFolders:
        for key, common in gameCommonFolders:
            folder = str(gameFolder) + str(common)
            if os.path.isdir(folder):
                for game in next(os.walk(folder))[1]:
                    if game not in linksList:
                        content = content + [folder + game]

    if not chooseNotInstalled:
        for key, steamFolder in steamGameFolders:
            if os.path.isdir(steamFolder):
               content = content + [steamFolder + "/"+ s for s in next(os.walk(steamFolder))[1]]
    else:
        content = content + ["steam:" + ":" + name + ":" + str(id) for id, name in steamOwnedGames]
                
    return content

def init(choosedgame):
    global __CHOOSEDGAME__
    __CHOOSEDGAME__ = choosedgame
 
