import sys

from aesgard.steam     import getownedgames
from aesgard.steam     import get_steam_game_ids
from aesgard.gog       import getGOGGames
from aesgard.gameutil  import prepareContent
from aesgard.gameutil  import preparelinksList
from aesgard.gameutil  import chooseGame
from aesgard.util      import writeListToFile
from aesgard.util      import writeTupleToFile
from aesgard.util      import LogException
from aesgard.database  import init as databaseInit
from aesgard.database  import importContentToDatabase as importContentToDatabase
from aesgard.ui        import showChoosedGame
from aesgard.config    import Config

def run(argv):
    __CONFIG__ = Config()
    __CONFIG__.read_config(argv)
    
    try:
        databaseInit(__CONFIG__.DatabaseServer, 
                     __CONFIG__.DatabaseUser, 
                     __CONFIG__.DatabasePassword, 
                     __CONFIG__.DatabaseName, 
                     __CONFIG__.DatabaseType)
    except Exception as e:
        LogException("Error initializing database!", e)
        return
    
    try:
        steamOwnedGames = getownedgames(__CONFIG__.ownedGamesURL,
                                        __CONFIG__.apikey, 
                                        __CONFIG__.steamid)
        steamGamesIds = get_steam_game_ids(steamOwnedGames).items();
    except Exception as e:
        LogException("Steam API not available!", e)
        steamOwnedGames = {}
        steamGamesIds = {}
        
    gogGames = getGOGGames(__CONFIG__.GOGDatabase)
        
    linksList = preparelinksList(__CONFIG__.foldersWithLinks, __CONFIG__.baseLinks)
    
    # Create game list from all sources
    content = list(set(
        prepareContent(
            __CONFIG__.gameFolders, 
            __CONFIG__.gameCommonFolders, 
            __CONFIG__.steamGameFolders, 
            linksList,
            steamGamesIds,
            __CONFIG__.chooseNotInstalled,
            __CONFIG__.removals,
            __CONFIG__.endswith)
        ))    
    
    # Writing files    
    if __CONFIG__.createFiles:
        writeListToFile(__CONFIG__.pathToSave + __CONFIG__.gamesFoundFileName, content)
        writeTupleToFile(__CONFIG__.pathToSave + __CONFIG__.steamGamesOwnedFileName, steamGamesIds)
        
    if __CONFIG__.importContentToDatabase:
        importContentToDatabase(content)

    choosedGame = chooseGame(content)
        
    print("You have " + str(len(content)) + " games to play!")
    print("CHOOSED -----------> " + choosedGame + " <-----------")
    showChoosedGame(choosedGame, steamOwnedGames)

if __name__ == '__main__':
    run(sys.argv)
