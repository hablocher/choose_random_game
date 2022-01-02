# -*- coding: utf-8 -*-
"""
Created on Sat Apr 24 18:56:44 2021

@author: Marcelo
"""
import jellyfish
import os
import sys
import win32com.client 

from aesgard.steam     import playgame
from aesgard.steam     import playgameid
from aesgard.database  import insertGameInfo
from aesgard.database  import findGameInfo

linkPrefix = "link::"

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

def startLink():
    if (__CHOOSEDGAME__.startswith(linkPrefix)):
        launch = __CHOOSEDGAME__[len(linkPrefix):]
        print("Calling '" + launch + "'")
        if (launch.endswith(".lnk") or launch.endswith(".url")):
            os.startfile(launch)
        else:
            os.startfile(launch + ".url")
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
           playgameid(playGameURL, __CHOOSEDGAME__[pos:])
           sys.exit(0) 
                   
def openDOSBOX(DOSBOXLocation, DOSBOXExecutable, DOSBOXParameters):
    if "dosbox" in __CHOOSEDGAME__:
        print("Executing DOXBOX Game '" + __CHOOSEDGAME__ + "'")
        posLastBar = __CHOOSEDGAME__.rfind("/")+1
        DOSBOXParameters = DOSBOXParameters.format('"cd ' + __CHOOSEDGAME__[posLastBar:] + '"')
        os.chdir(DOSBOXLocation)
        os.system(DOSBOXExecutable + " " + DOSBOXParameters)
        sys.exit(0) 

def findeXoDOSGame(EXODOSLocation):
    if "exodos" in __CHOOSEDGAME__:
        posLastBar = __CHOOSEDGAME__.rfind("/")+1
        gameLocation = EXODOSLocation + '/!dos/' + __CHOOSEDGAME__[posLastBar:]
        os.chdir(gameLocation)
        for file in os.listdir(gameLocation):
            if (file.lower() != 'install.bat' and file.lower().endswith('.bat')):
                file = '"' + file + '"'
                print("Executing eXoDOS Game " + file )
                os.startfile(file)
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
            linksList = linksList + [linkPrefix + baseLinks + link + "/" + s.lower() for s in next(os.walk(baseLinks + link))[2]]
        else:
            linksList = linksList + [linkPrefix + link + "/" + s.lower() for s in next(os.walk(link))[2]]
    
    for key, removal in removals:
        linksList = [g.replace(removal.lower(), '') for g in linksList]
    return linksList

def prepareContent(gameFolders, gameCommonFolders, steamGameFolders, linksList, steamOwnedGames, chooseNotInstalled):
    shell = win32com.client.Dispatch("WScript.Shell")
    content = []
    for key, gameFolder in gameFolders:
        for key, common in gameCommonFolders:
            folder = str(gameFolder) + str(common)
            if os.path.isdir(folder):
                for game in next(os.walk(folder))[1]:
                    content = content + [folder.lower() + game.lower()]

    for link in linksList:
        if (link.endswith(".lnk")):
            shortcut = shell.CreateShortCut(link[len(linkPrefix):])
            targetFolder = shortcut.Targetpath.lower().replace('\\','/')
            targetFolder = targetFolder[:targetFolder.rfind('/')]
            if targetFolder not in content:
                content = content + [link]
        else:
            content = content + [link]

    if not chooseNotInstalled:
        for key, steamFolder in steamGameFolders:
            if os.path.isdir(steamFolder):
               content = content + [steamFolder.lower() + "/"+ s.lower() for s in next(os.walk(steamFolder))[1]]
    else:
        content = content + ["steam:" + ":" + name + ":" + str(id) for id, name in steamOwnedGames]
                
    return content

def gameHasBeenPlayed(choosedGame):
    return findGameInfo(choosedGame)

def init(choosedgame):
    global __CHOOSEDGAME__
    __CHOOSEDGAME__ = choosedgame
    insertGameInfo(__CHOOSEDGAME__)
