import sys

from aesgard.steam     import getownedgames
from aesgard.steam     import get_steam_game_ids
from aesgard.gog       import getGOGGames
from aesgard.gameutil  import prepareContent
from aesgard.gameutil  import preparelinksList
from aesgard.gameutil  import chooseGame
from aesgard.util      import writeListToFile
from aesgard.util      import writeTupleToFile
from aesgard.util      import readConfigFile
from aesgard.util      import LogException
from aesgard.database  import init as databaseInit
from aesgard.ui        import showChoosedGame

def run(argv):
    config = readConfigFile(argv)
    
    apikey                  = config['STEAM']['apikey']
    steamid                 = config['STEAM']['steamid']
    ownedGamesURL           = config['STEAM']['ownedGamesURL']
    chooseNotInstalled      = config.getboolean('STEAM','chooseNotInstalled')

    baseLinks               = config['CONFIG']['baseLinks']
    onlyFavorites           = config['CONFIG']['onlyFavorites']

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

    choosedGame = chooseGame(content)
        
    print("You have " + str(len(content)) + " games to play!")
    print("CHOOSED -----------> " + choosedGame + " <-----------")
    showChoosedGame(choosedGame, steamOwnedGames, config)

if __name__ == '__main__':
    run(sys.argv)
