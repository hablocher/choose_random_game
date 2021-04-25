import random
import os
import sys
import configparser 

from aesgard.steam     import getownedgames
from aesgard.steam     import get_steam_game_ids
from aesgard.gameutil  import findLaunchAndStart
from aesgard.gameutil  import findSteamGameAndLaunch
from aesgard.gameutil  import openDOSBOX
from aesgard.gameutil  import executeEXE
from aesgard.gameutil  import prepareContent
from aesgard.gameutil  import preparelinksList

def run():
    config = configparser.ConfigParser()
    config.read("choose_random_game.ini")
    
    apikey                  = config['STEAM']['apikey']
    steamid                 = config['STEAM']['steamid']
    steamUserName           = config['STEAM']['username']
    ownedGamesURL           = config['STEAM']['ownedGamesURL']
    playGameURL             = config['STEAM']['playGameURL']
    chooseNotInstalled      = config.getboolean('STEAM','chooseNotInstalled')
    steamGamesOwnedInfoURL  = config['STEAM']['gamesInfoURL']

    baseLinks               = config['CONFIG']['baseLinks']
    shortcutExt             = config['CONFIG']['shortcutExt']
    DOSBOXShortcut          = config['CONFIG']['DOSBOXshortcut']

    pathToSave              = config['FILES']['pathToSave']
    gamesFoundFileName      = config['FILES']['gamesFoundFileName']
    steamGamesOwnedFileName = config['FILES']['gamesOwnedFileName']

    gameFolders             = config.items("GAMEFOLDERS")
    foldersWithLinks        = config.items("FOLDERSWITHLINKS")
    gameCommonFolders       = config.items("GAMECOMMONFOLDERS")
    steamGameFolders        = config.items("STEAMGAMEFOLDERS")
    removals                = config.items("REMOVALS")
    launchPrefixes          = config.items("LAUCHERPREFIXES")    
    
    steamOwnedGames = get_steam_game_ids(steamGamesOwnedInfoURL, steamUserName).items();
    linksList = preparelinksList(foldersWithLinks, baseLinks, removals)
    
    content = list(set(
        prepareContent(
            gameFolders, 
            gameCommonFolders, 
            steamGameFolders, 
            linksList,
            steamOwnedGames,
            chooseNotInstalled)
        ))    
    
    with open(pathToSave + gamesFoundFileName, 'w+', encoding="utf-8") as filehandle:  
        for listitem in content:
            filehandle.write('{}\n'.format(listitem))
    
    with open(pathToSave + steamGamesOwnedFileName, 'w+', encoding='utf-8') as filehandle:
        for id, name in steamOwnedGames:
            filehandle.write("{},{}\n".format(id, name))

    # Choosing
    random.shuffle(content)
    choosedGame = random.choice(content)
    
    print("You have " + str(len(content)) + " games to play!")
    print("CHOOSED -----------> " + choosedGame + " <-----------")

    # Executing
    findLaunchAndStart(choosedGame, launchPrefixes, shortcutExt)
    findSteamGameAndLaunch(getownedgames(ownedGamesURL, apikey, steamid), choosedGame, playGameURL, chooseNotInstalled)
    openDOSBOX(choosedGame, DOSBOXShortcut)
    executeEXE(choosedGame)

    # Fallback to opening the folder
    print("Opening folder '" + choosedGame + "'")
    os.startfile(choosedGame)
    sys.exit()
   
if __name__ == '__main__':
    run()
