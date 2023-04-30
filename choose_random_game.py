import random
import sys

from aesgard.steam     import getownedgames
from aesgard.steam     import get_steam_game_ids
from aesgard.gog       import getGOGGames
from aesgard.gameutil  import init as gameUtilInit
from aesgard.gameutil  import findLauncherAndStart
from aesgard.gameutil  import findSteamGameAndLaunch
from aesgard.gameutil  import openDOSBOX
from aesgard.gameutil  import findeXoDOSGame
from aesgard.gameutil  import executeEXE
from aesgard.gameutil  import startLink
from aesgard.gameutil  import prepareContent
from aesgard.gameutil  import preparelinksList
from aesgard.gameutil  import fallBackToGameFolder
from aesgard.gameutil  import gameHasBeenPlayed
from aesgard.util      import writeListToFile
from aesgard.util      import writeTupleToFile
from aesgard.util      import readConfigFile
from aesgard.util      import LogException
from aesgard.database  import init as databaseInit

def run(argv):
    config = readConfigFile(argv)
    
    apikey                  = config['STEAM']['apikey']
    steamid                 = config['STEAM']['steamid']
    ownedGamesURL           = config['STEAM']['ownedGamesURL']
    playGameURL             = config['STEAM']['playGameURL']
    chooseNotInstalled      = config.getboolean('STEAM','chooseNotInstalled')

    baseLinks               = config['CONFIG']['baseLinks']
    shortcutExt             = config['CONFIG']['shortcutExt']

    DOSBOXLocation          = config['DOSBOX']['DOSBOXLocation']
    DOSBOXParameters        = config['DOSBOX']['DOSBOXParameters']
    DOSBOXExecutable        = config['DOSBOX']['DOSBOXExecutable']

    EXODOSLocation          = config['EXODOS']['EXODOSLocation']

    createFiles             = config.getboolean('FILES','createFiles')
    pathToSave              = config['FILES']['pathToSave']
    gamesFoundFileName      = config['FILES']['gamesFoundFileName']
    steamGamesOwnedFileName = config['FILES']['gamesOwnedFileName']

    gameFolders             = config.items("GAMEFOLDERS")
    foldersWithLinks        = config.items("FOLDERSWITHLINKS")
    gameCommonFolders       = config.items("GAMECOMMONFOLDERS")
    steamGameFolders        = config.items("STEAMGAMEFOLDERS")
    removals                = config.items("REMOVALS")
    endswith                = config.items("ENDSWITH")
    launchPrefixes          = config.items("LAUCHERPREFIXES")    
    
    DatabaseServer          = config['DATABASE']['server']
    DatabaseUser            = config['DATABASE']['user']
    DatabasePassword        = config['DATABASE']['password']
    DatabaseName            = config['DATABASE']['name']
    DatabaseType            = config['DATABASE']['type']
    
    GOGDatabase             = config['GOG']['database']

    databaseInit(DatabaseServer, 
                 DatabaseUser, 
                 DatabasePassword, 
                 DatabaseName, 
                 DatabaseType)
    
    try:
        steamOwnedGames = getownedgames(ownedGamesURL, apikey, steamid)
        steamGamesIds = get_steam_game_ids(steamOwnedGames).items();
    except Exception as e:
        LogException("Steam API not available!", e)
        steamOwnedGames = {}
        steamGamesIds = {}
        
    gogGames = getGOGGames(GOGDatabase)
        
    linksList = preparelinksList(foldersWithLinks, baseLinks)
    
    # Create game list from all sources
    content = list(set(
        prepareContent(
            gameFolders, 
            gameCommonFolders, 
            steamGameFolders, 
            linksList,
            steamGamesIds,
            chooseNotInstalled,
            removals,
            endswith)
        ))    
    
    # Writing files    
    if createFiles:
        writeListToFile(pathToSave + gamesFoundFileName, content)
        writeTupleToFile(pathToSave + steamGamesOwnedFileName, steamGamesIds)

    # Choosing random game
    choosedGame = random.choice(content)
    while gameHasBeenPlayed(choosedGame):
        choosedGame = random.choice(content)        
    gameUtilInit(choosedGame)
    
    print("You have " + str(len(content)) + " games to play!")
    print("CHOOSED -----------> " + choosedGame + " <-----------")

    # Executing choosed game
    try:
        startLink()
        findLauncherAndStart(launchPrefixes, shortcutExt)
        findSteamGameAndLaunch(steamOwnedGames, playGameURL, chooseNotInstalled)
        openDOSBOX(DOSBOXLocation, DOSBOXExecutable, DOSBOXParameters)
        findeXoDOSGame(EXODOSLocation)
        executeEXE()
        fallBackToGameFolder()    
    except Exception as e:
        print("Can't start " + choosedGame + "(" + str(e) + ")")

    
if __name__ == '__main__':
    run(sys.argv)
