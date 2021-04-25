import random
import configparser 

from aesgard.steam     import getownedgames
from aesgard.steam     import get_steam_game_ids
from aesgard.gameutil  import findLaunchAndStart
from aesgard.gameutil  import findSteamGameAndLaunch
from aesgard.gameutil  import openDOSBOX
from aesgard.gameutil  import executeEXE
from aesgard.gameutil  import prepareContent
from aesgard.gameutil  import preparelinksList
from aesgard.gameutil  import fallBackToGameFolder
from aesgard.util      import writeListToFile
from aesgard.util      import writeTupleToFile

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
    createFiles             = config.getboolean('CONFIG','createFiles')

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
    
    # Create game list from all sources
    content = list(set(
        prepareContent(
            gameFolders, 
            gameCommonFolders, 
            steamGameFolders, 
            linksList,
            steamOwnedGames,
            chooseNotInstalled)
        ))    

    # Writing files    
    if createFiles:
        writeListToFile(pathToSave + gamesFoundFileName, content)
        writeTupleToFile(pathToSave + steamGamesOwnedFileName, steamOwnedGames)

    # Choosing game
    random.shuffle(content)
    choosedGame = random.choice(content)
    
    print("You have " + str(len(content)) + " games to play!")
    print("CHOOSED -----------> " + choosedGame + " <-----------")

    # Executing choosed game
    findLaunchAndStart(choosedGame, launchPrefixes, shortcutExt)
    findSteamGameAndLaunch(getownedgames(ownedGamesURL, apikey, steamid), choosedGame, playGameURL, chooseNotInstalled)
    openDOSBOX(choosedGame, DOSBOXShortcut)
    executeEXE(choosedGame)
    fallBackToGameFolder(choosedGame)
 
if __name__ == '__main__':
    run()
