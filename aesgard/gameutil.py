# -*- coding: utf-8 -*-
"""
Created on Sat Apr 24 18:56:44 2021

@author: Marcelo
"""
import random
import jellyfish
import os
import sys
import win32com.client 
from datetime import datetime

from PIL import Image
import requests
from io import BytesIO

from aesgard.steam     import playgame
from aesgard.steam     import playgameid
from aesgard.database  import insertGameInfo
from aesgard.database  import findGameInfo
from aesgard.winicon   import extract_icon, IconSize
from aesgard.util      import win32_icon_to_image
from aesgard.util      import LogException
from aesgard.config    import Config

linkPrefix = "link::"
steamPrefix = "steam:"

__CONFIG__ = Config()
__CONFIG__.read_config(sys.argv)

def normalizeString(text):
    return text.replace(" ","").replace(":","").replace("-","").replace("'","").replace(",","").replace("!","").replace("+","").replace("(","").replace(")","").lower()

def checkExeFile(launch, choosed):
    if jellyfish.levenshtein_distance(launch, choosed) == 2: 
        return True
    if 'launcher.exe' == launch:
        return True
    return False    

def findLauncherAndStart(launcherPrefixes, shortcutExt):
    launch = findLauncher(__CHOOSEDGAME__, launcherPrefixes, shortcutExt)
    if  launch != None:
        print("Calling '" + launch + "'")
        os.chdir(__CHOOSEDGAME__)
        os.startfile(launch)
        sys.exit(0) 
                   
def findLauncher(choosedGame, launcherPrefixes, shortcutExt):
    if os.path.isdir(choosedGame):
        for launch in next(os.walk(choosedGame))[2]:
            for key, prefix in launcherPrefixes:
                if (launch.lower().startswith(prefix.lower()) and launch.lower().endswith(shortcutExt)): 
                    return launch
    return None

def startLink():
    url = findClientURL(__CHOOSEDGAME__)
    if url != None:
       os.startfile(url)
       sys.exit(0) 
        
def findClientURL(choosedGame):
    if (choosedGame.startswith(linkPrefix)):
        launch = choosedGame[len(linkPrefix):]
        if (launch.endswith(__CONFIG__.shortcutExt) or launch.endswith(".url")):
            return launch
        shell = win32com.client.Dispatch("WScript.Shell")
        linkFile = launch + __CONFIG__.shortcutExt
        shortcut = shell.CreateShortcut(linkFile)
        for key, client in __CONFIG__.otherClients:
            if (shortcut.Targetpath.startswith(client)):
                return shortcut.Targetpath
        linkFile = launch + ".url"
        shortcut = shell.CreateShortcut(linkFile)
        for key, client in __CONFIG__.otherClients:
            if (shortcut.Targetpath.startswith(client)):
                return shortcut.Targetpath
    return None
                   
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
       if __CHOOSEDGAME__.startswith(steamPrefix):
           pos = __CHOOSEDGAME__.rfind(":") + 1
           print("Calling STEAM app ID " + __CHOOSEDGAME__)
           playgameid(playGameURL, __CHOOSEDGAME__[pos:])
           sys.exit(0) 

def findGameIcon(steamGames, imageGameURL, choosedGame):
    global __CONFIG__   
    image = Image.new("RGB", (128, 128), (255, 255, 255))
    if choosedGame.startswith(steamPrefix):
        begin = choosedGame.find(":") + 1
        end   = choosedGame.rfind(":")
        choosedGame = choosedGame[begin:end]
        for steamGame in steamGames:  
            if (steamGame['name'] == choosedGame):
                url = imageGameURL.format(steamGame['appid'])#, steamGame['img_icon_url'])
                response = requests.get(url)
                image = Image.open(BytesIO(response.content))
                break
    else:
         if 'exodos' in choosedGame:
             response = requests.get(__CONFIG__.EXODOSImageURL)
             return Image.open(BytesIO(response.content))
         try:
             shell = win32com.client.Dispatch("WScript.Shell")
             launch = findLauncher(choosedGame, __CONFIG__.launcherPrefixes, __CONFIG__.shortcutExt)
             if launch != None:
                 shortcut = shell.CreateShortcut(choosedGame + '/' + launch)
                 return win32_icon_to_image(extract_icon(shortcut.Targetpath, IconSize.LARGE), IconSize.LARGE).resize((128, 128))
             exeFile = findEXE(choosedGame)
             if exeFile != None:
                 return win32_icon_to_image(extract_icon(exeFile[0], IconSize.LARGE), IconSize.LARGE).resize((128, 128))
         except WindowsError as we:
             LogException("Error reading ICON image from EXE!", we)
             return image
    return image
               
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
    exeInfo = findEXE(__CHOOSEDGAME__)
    if exeInfo != None:
        os.chdir(exeInfo[1])
        os.startfile(exeInfo[0])
        sys.exit(0) 

def findEXE(choosedGame):
    posLastBar = choosedGame.rfind("/")
    exeCount = 0
    exeFolder = ""
    exeFile = ""
    if findClientURL(choosedGame) != None:
        return None
    for launch in next(os.walk(choosedGame))[2]:
        if launch.lower().endswith('.exe'):
            exeCount += 1
            exeFolder = choosedGame
            exeFile = launch
            if checkExeFile(exeFile.lower(), choosedGame[posLastBar:].lower()):
                print("Calling EXE '" + launch + "'")
                return (exeFile, exeFolder)           
    if (exeCount == 1):
        if not 'uninst' in exeFile:
            print("Calling EXE '" + exeFile + "'")
            return (exeFile, exeFolder)
    return None

def fallBackToGameFolder():
    # Fallback and open the game folder
    print("Opening folder '" + __CHOOSEDGAME__ + "'")
    os.startfile(__CHOOSEDGAME__)
    sys.exit(0)
    
def preparelinksList(foldersWithLinks, baseLinks):
    linksList = []
    for key, link in foldersWithLinks:
        if baseLinks:
            linksList = linksList + [linkPrefix + baseLinks + link + "/" + s.lower() for s in next(os.walk(r'' + baseLinks + link))[2]]
        else:
            linksList = linksList + [linkPrefix + link + "/" + s.lower() for s in next(os.walk(link))[2]]

    return linksList

def prepareContent(gameFolders, 
                   gameCommonFolders, 
                   steamGameFolders, 
                   linksList, 
                   steamGamesIds, 
                   chooseNotInstalled,
                   removals,
                   endswith):
    content = []
    ends = tuple(t[1].lower() for t in endswith)

    for key, gameFolder in gameFolders:
        for key, common in gameCommonFolders:
            folder = str(gameFolder) + str(common)
            if os.path.isdir(folder):
                for game in next(os.walk(folder))[1]:
                    g = folder.lower() + game.lower()
                    if not g.endswith(ends):
                        content = content + [g]

    for link in linksList:
        content = content + [link]

    if not chooseNotInstalled:
        for key, steamFolder in steamGameFolders:
            if os.path.isdir(steamFolder):
               content = content + [steamFolder.lower() + "/"+ s.lower() for s in next(os.walk(steamFolder))[1]]
    else:
        content = content + [steamPrefix + name + ":" + str(id) for id, name in steamGamesIds]
                
    for key, removal in removals:
        content = [g.replace(removal, '') for g in content]
        
    content = [g.replace("'","''") for g in content]
    
    content = list(filter(None, content))
    
    return content

def gameHasBeenPlayed(choosedGame):
    return findGameInfo(choosedGame) != None

def init(choosedgame):
    global __CHOOSEDGAME__
    __CHOOSEDGAME__ = choosedgame
    insertGameInfo(__CHOOSEDGAME__)
    
def executeGame(choosedGame, steamOwnedGames):
    # Executing choosed game
    try:
        init(choosedGame)
        startLink()
        findLauncherAndStart(__CONFIG__.launcherPrefixes, __CONFIG__.shortcutExt)
        findSteamGameAndLaunch(steamOwnedGames, __CONFIG__.playGameURL, __CONFIG__.chooseNotInstalled)
        findeXoDOSGame(__CONFIG__.EXODOSLocation)
        openDOSBOX(__CONFIG__.DOSBOXLocation, __CONFIG__.DOSBOXExecutable, __CONFIG__.DOSBOXParameters)
        executeEXE()
        fallBackToGameFolder()    
    except Exception as e:
        print("Can't start " + choosedGame + "(" + str(e) + ")")
    
# Choosing random game
def chooseGame(content):
    curr_dt = datetime.now()
    random.seed(int(round(curr_dt.timestamp())))
    choosedGame = random.choice(content)
    for x in range(len(content)):
        if gameHasBeenPlayed(choosedGame):
            choosedGame = random.choice(content)     
        else:
            break
    return choosedGame
