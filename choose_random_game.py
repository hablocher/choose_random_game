import random
import sys


from aesgard.steam     import getownedgames
from aesgard.steam     import get_steam_game_ids
from aesgard.gameutil  import init as gameUtilInit
from aesgard.gameutil  import findLauncherAndStart
from aesgard.gameutil  import findSteamGameAndLaunch
from aesgard.gameutil  import openDOSBOX
from aesgard.gameutil  import executeEXE
from aesgard.gameutil  import prepareContent
from aesgard.gameutil  import preparelinksList
from aesgard.gameutil  import fallBackToGameFolder
from aesgard.util      import writeListToFile
from aesgard.util      import writeTupleToFile
from aesgard.util      import readConfigFile
from aesgard.database  import init as databaseInit

def run(argv):
    config = readConfigFile(argv)
    
    apikey                  = config['STEAM']['apikey']
    steamid                 = config['STEAM']['steamid']
    steamUserName           = config['STEAM']['username']
    ownedGamesURL           = config['STEAM']['ownedGamesURL']
    playGameURL             = config['STEAM']['playGameURL']
    chooseNotInstalled      = config.getboolean('STEAM','chooseNotInstalled')
    steamGamesOwnedInfoURL  = config['STEAM']['gamesInfoURL']

    baseLinks               = config['CONFIG']['baseLinks']
    shortcutExt             = config['CONFIG']['shortcutExt']

    DOSBOXLocation          = config['DOSBOX']['DOSBOXLocation']
    DOSBOXParameters        = config['DOSBOX']['DOSBOXParameters']
    DOSBOXExecutable        = config['DOSBOX']['DOSBOXExecutable']

    createFiles             = config.getboolean('FILES','createFiles')
    pathToSave              = config['FILES']['pathToSave']
    gamesFoundFileName      = config['FILES']['gamesFoundFileName']
    steamGamesOwnedFileName = config['FILES']['gamesOwnedFileName']

    gameFolders             = config.items("GAMEFOLDERS")
    foldersWithLinks        = config.items("FOLDERSWITHLINKS")
    gameCommonFolders       = config.items("GAMECOMMONFOLDERS")
    steamGameFolders        = config.items("STEAMGAMEFOLDERS")
    removals                = config.items("REMOVALS")
    launchPrefixes          = config.items("LAUCHERPREFIXES")    
    
    DatabaseServer          = config['DATABASE']['server']
    DatabaseUser            = config['DATABASE']['user']
    DatabasePassword        = config['DATABASE']['password']
    DatabaseName            = config['DATABASE']['name']
    
    databaseInit(DatabaseServer, DatabaseUser, DatabasePassword, DatabaseName)
    
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
    gameUtilInit(choosedGame)
    
    print("You have " + str(len(content)) + " games to play!")
    print("CHOOSED -----------> " + choosedGame + " <-----------")

    # Executing choosed game
    findLauncherAndStart(launchPrefixes, shortcutExt)
    findSteamGameAndLaunch(getownedgames(ownedGamesURL, apikey, steamid), playGameURL, chooseNotInstalled)
    openDOSBOX(DOSBOXLocation, DOSBOXExecutable, DOSBOXParameters)
    executeEXE()
    fallBackToGameFolder()
 
if __name__ == '__main__':
    run(sys.argv)
